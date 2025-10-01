"""
Task Queue Service for async chat processing
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.models.chat_task import ChatTask, TaskStatus
from app.services.poem_service import poem_service
from app.core.database import get_database_session, get_async_session
from app.utils.timeout_utils import (
    with_timeout, run_with_timeout, timeout_context, TimeoutError,
    rag_circuit_breaker, llm_circuit_breaker, with_circuit_breaker
)
from app.services.task_worker_pool import TaskWorkerPool
from app.utils.progress_tracker import (
    create_progress_aware_task, progress_manager, StreamingProgressTracker
)
from app.utils.streaming_processor import (
    create_streaming_processor, cleanup_streaming_processor
)
import uuid
import json


logger = logging.getLogger(__name__)


class TaskQueueService:
    """Service for managing async task processing"""

    def __init__(self):
        self.active_tasks: Dict[str, ChatTask] = {}
        self.sse_connections: Dict[str, List] = {}  # task_id -> list of response objects
        self.is_processing = False
        self.task_timeout = 120.0  # 2 minutes timeout per task
        self.rag_timeout = 30.0  # 30 seconds for RAG operations
        self.llm_timeout = 60.0  # 1 minute for LLM operations

        # Worker pool for concurrent processing
        self.worker_pool = TaskWorkerPool(
            max_workers=3,
            worker_timeout=self.task_timeout
        )

    async def create_task(
        self,
        user_id: int,
        deity_id: str,
        fortune_number: int,
        question: str,
        context: dict = None,
        db: AsyncSession = None
    ) -> ChatTask:
        """Create a new chat task"""
        task = ChatTask(
            user_id=user_id,
            deity_id=deity_id,
            fortune_number=fortune_number,
            question=question,
            context=context or {}
        )

        if db:
            db.add(task)
            await db.commit()
            await db.refresh(task)

        logger.info(f"Created task {task.task_id} for user {user_id}")
        return task

    async def get_task(self, task_id: str, db: AsyncSession) -> Optional[ChatTask]:
        """Get task by ID"""
        result = await db.execute(select(ChatTask).where(ChatTask.task_id == task_id))
        return result.scalar_one_or_none()

    async def get_user_tasks(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
        db: AsyncSession = None
    ) -> List[ChatTask]:
        """Get tasks for a user"""
        result = await db.execute(
            select(ChatTask)
            .where(ChatTask.user_id == user_id)
            .order_by(ChatTask.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def start_processing(self):
        """Start the background task processor with worker pool"""
        if self.is_processing:
            return

        self.is_processing = True
        logger.info("Starting task queue processor with worker pool")

        # Start the worker pool
        await self.worker_pool.start()

        # Start the task dispatcher
        asyncio.create_task(self._task_dispatcher())

        logger.info("Task queue processor started successfully")

    async def _task_dispatcher(self):
        """Dispatch tasks to the worker pool"""
        while self.is_processing:
            try:
                await self.process_queued_tasks()
                await asyncio.sleep(2)  # Check for new tasks every 2 seconds
            except Exception as e:
                logger.error(f"Error in task dispatcher: {e}")
                await asyncio.sleep(5)  # Wait longer on error

    async def stop_processing(self):
        """Stop the background task processor and worker pool"""
        self.is_processing = False
        logger.info("Stopping task queue processor")

        # Stop the worker pool
        await self.worker_pool.stop()

        logger.info("Task queue processor stopped")

    async def process_queued_tasks(self):
        """Process queued tasks using worker pool"""
        # Get database session
        async for db in get_database_session():
            try:
                # Find queued tasks
                result = await db.execute(
                    select(ChatTask)
                    .where(ChatTask.status == TaskStatus.QUEUED)
                    .order_by(ChatTask.created_at)
                    .limit(10)  # Get more tasks to choose from
                )
                queued_tasks = result.scalars().all()

                # Submit tasks to worker pool
                for task in queued_tasks:
                    if (task.task_id not in self.active_tasks and
                        not self.worker_pool.is_task_active(task.task_id)):

                        # Submit task to worker pool with streaming processor
                        await self.worker_pool.submit_task(
                            task.task_id,
                            self.process_task,
                            task.task_id
                        )

                        # Track the task
                        self.active_tasks[task.task_id] = task

                        logger.info(f"Submitted task {task.task_id} to worker pool")

                break  # Exit the async generator
            except Exception as e:
                logger.error(f"Error getting queued tasks: {e}")

    async def _process_task_with_timeout(self, task_id: str):
        """Process a single task with timeout protection"""
        try:
            await run_with_timeout(
                self.process_task(task_id),
                timeout_seconds=self.task_timeout,
                raise_on_timeout=True
            )
        except TimeoutError:
            logger.error(f"Task {task_id} timed out after {self.task_timeout}s")
            await self._handle_task_timeout(task_id)
        except Exception as e:
            logger.error(f"Unexpected error in task {task_id}: {e}")
        finally:
            # Ensure task is cleaned up from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

            # Note: Worker pool handles its own cleanup of task tracking

    async def _handle_task_timeout(self, task_id: str):
        """Handle task timeout by updating status and notifying clients"""
        try:
            async with get_async_session() as db:
                task = await self.get_task(task_id, db)
                if task:
                    task.set_error(f"Task timed out after {self.task_timeout} seconds")
                    await db.merge(task)
                    await db.commit()

                # Send timeout error to SSE clients
                await self.send_sse_event(task_id, {
                    "type": "error",
                    "error": f"Request timed out after {self.task_timeout} seconds. Please try again.",
                    "retry_allowed": True
                })
        except Exception as e:
            logger.error(f"Error handling timeout for task {task_id}: {e}")

    async def process_task(self, task_id: str):
        """Process a single task with true real-time streaming"""
        task = None
        start_time = time.time()
        streaming_processor = None

        try:
            # Create streaming processor for true real-time updates
            streaming_processor = create_streaming_processor(
                task_id,
                self.send_sse_event,
                smart=True
            )

            # Create dedicated database session for this task
            async with get_async_session() as db:
                # Get task with timeout
                await streaming_processor.send_update("initializing", 2, "🔄 初始化任務...")

                async with timeout_context(5.0, "task_retrieval"):
                    task = await self.get_task(task_id, db)
                    if not task:
                        logger.warning(f"Task {task_id} not found")
                        return

                    if task.status != TaskStatus.QUEUED:
                        logger.warning(f"Task {task_id} is not queued (status: {task.status})")
                        return

                self.active_tasks[task_id] = task
                logger.info(f"Processing task {task_id}: {task.question[:50]}...")

                # Step 1: Initial setup with streaming
                await streaming_processor.send_update("processing", 5, "🚀 啟動處理流程...")
                await self.update_task_progress(task, TaskStatus.PROCESSING, 10, "Starting analysis...", db)

                # Step 2: Stream RAG processing
                await self.update_task_progress(task, TaskStatus.ANALYZING_RAG, 15, "Analyzing fortune context...", db)

                poem_data = await streaming_processor.adaptive_stream_processing(
                    self._get_poem_data_blocking,
                    "RAG檢索",
                    15, 50,
                    "rag",
                    task
                )

                # Step 3: Stream LLM generation
                await self.update_task_progress(task, TaskStatus.GENERATING_LLM, 55, "Consulting divine wisdom...", db)

                response_text = await streaming_processor.adaptive_stream_processing(
                    self._generate_response_blocking,
                    "LLM推理",
                    55, 90,
                    "llm",
                    task, poem_data
                )

                confidence = 75 + (hash(task.question) % 25)  # Mock confidence 75-99

                # Step 4: Pre-save validation (Database Protection Layer)
                await streaming_processor.send_update("validating", 90, "🔍 驗證報告完整性...")
                validation_result = await self._validate_response_before_save(task_id, response_text)

                if not validation_result["is_valid"]:
                    error_msg = f"Response validation failed: {validation_result['error']}"

                    # Log database validation failure with detailed metrics
                    logger.error(
                        f"DATABASE_VALIDATION_FAILURE: Report failed final validation",
                        extra={
                            "task_id": task_id,
                            "user_id": task.user_id,
                            "deity_id": task.deity_id,
                            "fortune_number": task.fortune_number,
                            "validation_type": validation_result.get('validation_type', 'unknown'),
                            "error_details": validation_result.get('error', ''),
                            "empty_fields": validation_result.get('empty_fields', []),
                            "missing_keys": validation_result.get('missing_keys', []),
                            "processing_time_ms": int((time.time() - start_time) * 1000),
                            "metric_type": "database_validation_failure",
                            "should_refund": True
                        }
                    )

                    # Mark task as failed and potentially refund coins
                    task.set_error(error_msg)
                    await db.commit()

                    await streaming_processor.send_update("error", 0, f"❌ 報告驗證失敗: {validation_result['error']}")

                    await self.send_sse_event(task_id, {
                        "type": "error",
                        "error": error_msg,
                        "retry_allowed": True,
                        "should_refund": True  # Signal that coins should be refunded
                    })
                    return

                # Step 5: Finalization with streaming
                await streaming_processor.send_update("finalizing", 95, "📝 完成最終處理...")
                await self.update_task_progress(task, TaskStatus.COMPLETED, 100, "Response generated successfully", db)

                # Set result
                task.set_result(
                    response_text=response_text,
                    confidence=confidence,
                    sources_used=["RAG Analysis", "Traditional Interpretation", poem_data.temple]
                )

                # Save final result
                await db.commit()

                # Auto-generate FAQ from completed task
                try:
                    await self._auto_generate_faq(task, db)
                except Exception as faq_error:
                    logger.error(f"Failed to auto-generate FAQ for task {task_id}: {faq_error}")

                processing_time = int((time.time() - start_time) * 1000)

                # Log successful completion with comprehensive metrics
                logger.info(
                    f"TASK_SUCCESS: Report generation completed successfully",
                    extra={
                        "task_id": task_id,
                        "user_id": task.user_id,
                        "deity_id": task.deity_id,
                        "fortune_number": task.fortune_number,
                        "question_length": len(task.question),
                        "response_length": len(response_text),
                        "processing_time_ms": processing_time,
                        "confidence": confidence,
                        "validation_stats": validation_result.get('content_stats', {}),
                        "sources_used": task.sources_used,
                        "metric_type": "task_success"
                    }
                )

                # Final streaming update
                await streaming_processor.send_update("completed", 100, "🎉 解釋生成完成！")

                # Send completion event to SSE clients
                await self.send_sse_event(task_id, {
                    "type": "complete",
                    "result": {
                        "response": response_text,
                        "confidence": confidence,
                        "sources_used": task.sources_used,
                        "processing_time_ms": processing_time,
                        "can_generate_report": True
                    }
                })

        except TimeoutError as e:
            logger.error(f"Timeout processing task {task_id}: {e}")
            if streaming_processor:
                await streaming_processor.send_update("error", 0, f"⏰ 處理超時: {str(e)}")
            raise  # Re-raise to be handled by timeout wrapper
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            if streaming_processor:
                await streaming_processor.send_update("error", 0, f"❌ 處理錯誤: {str(e)}")

            # Update task with error using a new session
            try:
                async with get_async_session() as db:
                    if task_id in self.active_tasks:
                        task = self.active_tasks[task_id]
                        task.set_error(str(e))
                        await db.merge(task)  # Use merge to handle detached instance
                        await db.commit()

                    # Send error event to SSE clients
                    await self.send_sse_event(task_id, {
                        "type": "error",
                        "error": str(e),
                        "retry_allowed": True
                    })
            except Exception as commit_error:
                logger.error(f"Failed to save error state for task {task_id}: {commit_error}")

        finally:
            # Clean up streaming processor
            if streaming_processor:
                cleanup_streaming_processor(task_id)

    @with_circuit_breaker(rag_circuit_breaker, fallback_value=None)
    async def _get_poem_data_blocking(self, task: ChatTask):
        """Blocking poem data retrieval (to be called by streaming processor)"""
        async with timeout_context(self.rag_timeout, "poem_data_retrieval"):
            from app.services.deity_service import deity_service

            logger.info(f"[MAPPING] Original deity_id: '{task.deity_id}'")
            temple_name = deity_service.get_temple_name(task.deity_id) or task.deity_id
            logger.info(f"[MAPPING] Mapped temple_name: '{temple_name}'")

            poem_id = f"{temple_name}_{task.fortune_number}"
            logger.info(f"[MAPPING] Generated poem_id: '{poem_id}'")

            # Ensure poem service is initialized before lookup
            await poem_service.ensure_initialized()
            poem_data = await poem_service.get_poem_by_id(poem_id)

            if not poem_data:
                logger.error(f"[MAPPING] Poem not found with ID: '{poem_id}' - checking available poems")
                # Try to get available poems for debugging
                from fortune_module.unified_rag import UnifiedRAGHandler
                rag = UnifiedRAGHandler()
                available_temples = rag.get_collection_stats().get("temple_list", [])
                logger.error(f"[MAPPING] Available temples: {available_temples}")
                raise Exception(f"Fortune not found: {poem_id} (Available temples: {available_temples})")
            else:
                logger.info(f"[MAPPING] Successfully found poem: {poem_data.temple}#{poem_data.poem_id}")
                return poem_data

    @with_circuit_breaker(llm_circuit_breaker, fallback_value="I apologize, but I'm experiencing technical difficulties. Please try again later.")
    async def _generate_response_blocking(self, task: ChatTask, poem_data) -> str:
        """Blocking response generation (to be called by streaming processor)"""
        async with timeout_context(self.llm_timeout, "llm_response_generation"):
            result = await self.generate_response(task, poem_data)
            return result

    async def update_task_progress(
        self,
        task: ChatTask,
        status: TaskStatus,
        progress: int,
        message: str,
        db: AsyncSession
    ):
        """Update task progress and notify SSE clients"""
        task.update_progress(status, progress, message)
        await db.commit()

        # Send progress event to SSE clients
        await self.send_sse_event(task.task_id, {
            "type": "progress",
            "status": status.value,
            "progress": progress,
            "message": message
        })

    async def generate_response(self, task: ChatTask, poem_data) -> str:
        """Generate AI response for the task using the poem service (RAG + LLM)."""
        try:
            # Determine language preference if provided
            language = "en"
            try:
                if isinstance(task.context, dict) and task.context.get("language"):
                    language = str(task.context.get("language"))
            except Exception:
                pass

            result = await poem_service.generate_fortune_interpretation(
                poem_data=poem_data,
                question=task.question,
                language=language
            )
            return result.interpretation
        except Exception as e:
            logger.error(f"LLM generation failed, falling back to simple response: {e}")
            # Fallback simple message to avoid empty output
            return (
                f"Regarding your question '{task.question}', this fortune emphasizes patience, clarity, "
                f"and steady progress. Reflect on the poem '{poem_data.title}' for guidance."
            )

    def add_sse_connection(self, task_id: str, response_obj):
        """Add SSE connection for a task"""
        if task_id not in self.sse_connections:
            self.sse_connections[task_id] = []
        self.sse_connections[task_id].append(response_obj)
        logger.info(f"Added SSE connection for task {task_id}")

    def remove_sse_connection(self, task_id: str, response_obj):
        """Remove SSE connection for a task"""
        if task_id in self.sse_connections:
            try:
                self.sse_connections[task_id].remove(response_obj)
                if not self.sse_connections[task_id]:
                    del self.sse_connections[task_id]
            except ValueError:
                pass

    async def send_sse_event(self, task_id: str, data: dict):
        """Send SSE event to all connected clients for a task"""
        if task_id not in self.sse_connections:
            return

        import json
        event_data = f"data: {json.dumps(data)}\n\n"

        try:
            # Lightweight debug log to trace timing of outbound SSE
            logger.debug(
                f"SSE send -> task={task_id} type={data.get('type')} at {datetime.now().isoformat()} to {len(self.sse_connections.get(task_id, []))} clients"
            )
        except Exception:
            pass

        # Send to all connected clients
        for response_obj in self.sse_connections[task_id][:]:  # Copy list to avoid modification during iteration
            try:
                await response_obj.send(event_data)
            except Exception as e:
                logger.warning(f"Failed to send SSE event to client: {e}")
                self.remove_sse_connection(task_id, response_obj)

    async def _validate_response_before_save(self, task_id: str, response_text: str) -> Dict[str, Any]:
        """Final validation before saving to database - Database Protection Layer."""
        required_keys = [
            "LineByLineInterpretation",
            "OverallDevelopment",
            "PositiveFactors",
            "Challenges",
            "SuggestedActions",
            "SupplementaryNotes",
            "Conclusion"
        ]

        try:
            # Parse JSON
            try:
                parsed_response = json.loads(response_text)
            except json.JSONDecodeError as e:
                return {
                    "is_valid": False,
                    "error": f"Invalid JSON structure: {str(e)}",
                    "validation_type": "json_parse_error"
                }

            # Check structure
            if not isinstance(parsed_response, dict):
                return {
                    "is_valid": False,
                    "error": "Response is not a JSON object",
                    "validation_type": "structure_error"
                }

            # Check required keys
            missing_keys = [key for key in required_keys if key not in parsed_response]
            if missing_keys:
                return {
                    "is_valid": False,
                    "error": f"Missing required keys: {missing_keys}",
                    "validation_type": "missing_keys",
                    "missing_keys": missing_keys
                }

            # Check for empty values
            empty_fields = []
            for key in required_keys:
                value = parsed_response.get(key, "")
                if not isinstance(value, str) or not value.strip():
                    empty_fields.append(key)

            if empty_fields:
                return {
                    "is_valid": False,
                    "error": f"Empty or invalid fields: {empty_fields}",
                    "validation_type": "empty_fields",
                    "empty_fields": empty_fields
                }

            # Check minimum content length
            short_fields = []
            min_lengths = {
                "LineByLineInterpretation": 50,  # Reduced for database layer
                "OverallDevelopment": 30,
                "PositiveFactors": 30,
                "Challenges": 30,
                "SuggestedActions": 30,
                "SupplementaryNotes": 20,
                "Conclusion": 20
            }

            for key, min_length in min_lengths.items():
                value = parsed_response.get(key, "")
                if len(value.strip()) < min_length:
                    short_fields.append(f"{key} ({len(value.strip())}/{min_length})")

            if short_fields:
                return {
                    "is_valid": False,
                    "error": f"Fields too short: {short_fields}",
                    "validation_type": "content_too_short",
                    "short_fields": short_fields
                }

            # Enhanced quality checks
            quality_issues = await self._check_database_content_quality(parsed_response, task_id)
            if quality_issues:
                return {
                    "is_valid": False,
                    "error": f"Content quality issues: {quality_issues}",
                    "validation_type": "quality_validation",
                    "quality_issues": quality_issues
                }

            # Log successful database validation with metrics
            content_stats = {
                "total_length": len(response_text),
                "field_lengths": {key: len(str(parsed_response.get(key, ""))) for key in required_keys}
            }

            logger.info(
                f"DATABASE_VALIDATION_SUCCESS: Report passed final validation",
                extra={
                    "task_id": task_id,
                    "total_content_length": content_stats["total_length"],
                    "field_lengths": content_stats["field_lengths"],
                    "min_field_length": min(content_stats["field_lengths"].values()),
                    "max_field_length": max(content_stats["field_lengths"].values()),
                    "avg_field_length": sum(content_stats["field_lengths"].values()) / len(content_stats["field_lengths"]),
                    "metric_type": "database_validation_success"
                }
            )

            return {
                "is_valid": True,
                "error": None,
                "validation_type": "success",
                "content_stats": content_stats
            }

        except Exception as e:
            logger.error(f"Database validation error for task {task_id}: {e}")
            return {
                "is_valid": False,
                "error": f"Validation exception: {str(e)}",
                "validation_type": "validation_exception"
            }

    async def _check_database_content_quality(self, parsed_response: dict, task_id: str) -> List[str]:
        """Database-level content quality validation (final check)."""
        quality_issues = []

        line_by_line = parsed_response.get("LineByLineInterpretation", "")

        # Check for fallback content (most critical)
        critical_fallback_indicators = [
            "due to technical difficulties",
            "cannot provide detailed",
            "simplified due to technical",
            "由於技術困難",
            "技術問題"
        ]

        fallback_count = sum(1 for indicator in critical_fallback_indicators if indicator in line_by_line.lower())
        if fallback_count >= 1:
            quality_issues.append(f"Contains fallback/technical difficulty content ({fallback_count} indicators)")
            logger.warning(f"[DB_QUALITY] Task {task_id} contains fallback content: {line_by_line[:200]}...")

        # Check for proper line structure (critical for line-by-line interpretation)
        has_proper_lines = any(marker in line_by_line for marker in ["Line 1:", "Line 2:", "Line 3:", "第一句:", "第二句:"])
        if not has_proper_lines:
            quality_issues.append("LineByLineInterpretation lacks proper line-by-line structure")

        # Check for excessive generic content
        generic_phrases = [
            "wisdom guidance",
            "this fortune contains",
            "maintain patience",
            "step by step",
            "overall meaning"
        ]

        generic_count = sum(1 for phrase in generic_phrases if phrase in line_by_line.lower())
        if generic_count >= 4:  # Very high threshold for database level
            quality_issues.append(f"Overly generic content ({generic_count} generic phrases)")

        return quality_issues

    def get_service_metrics(self) -> Dict[str, Any]:
        """Get comprehensive service metrics"""
        pool_metrics = self.worker_pool.get_metrics()

        return {
            "task_queue_service": {
                "is_processing": self.is_processing,
                "active_tasks_count": len(self.active_tasks),
                "sse_connections_count": len(self.sse_connections),
                "timeouts": {
                    "task_timeout": self.task_timeout,
                    "rag_timeout": self.rag_timeout,
                    "llm_timeout": self.llm_timeout
                }
            },
            "worker_pool": pool_metrics,
            "timestamp": datetime.now().isoformat()
        }

    async def get_task_statistics(self, db: AsyncSession, hours: int = 24) -> Dict[str, Any]:
        """Get task processing statistics for the last N hours"""
        from datetime import timedelta
        from sqlalchemy import func

        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # Get task counts by status
            result = await db.execute(
                select(
                    ChatTask.status,
                    func.count(ChatTask.task_id).label('count')
                )
                .where(ChatTask.created_at >= cutoff_time)
                .group_by(ChatTask.status)
            )
            status_counts = {status.value: 0 for status in TaskStatus}
            for row in result:
                status_counts[row.status.value] = row.count

            # Get average processing time for completed tasks
            result = await db.execute(
                select(
                    func.avg(ChatTask.processing_time_ms).label('avg_time')
                )
                .where(
                    ChatTask.status == TaskStatus.COMPLETED,
                    ChatTask.created_at >= cutoff_time,
                    ChatTask.processing_time_ms.isnot(None)
                )
            )
            avg_processing_time = result.scalar() or 0

            # Get error distribution
            result = await db.execute(
                select(
                    func.substring(ChatTask.error_message, 1, 50).label('error_type'),
                    func.count(ChatTask.task_id).label('count')
                )
                .where(
                    ChatTask.status == TaskStatus.FAILED,
                    ChatTask.created_at >= cutoff_time,
                    ChatTask.error_message.isnot(None)
                )
                .group_by(func.substring(ChatTask.error_message, 1, 50))
                .limit(10)
            )
            error_types = [{
                'error_type': row.error_type,
                'count': row.count
            } for row in result]

            return {
                'period_hours': hours,
                'task_counts': status_counts,
                'avg_processing_time_ms': round(avg_processing_time, 2),
                'error_types': error_types,
                'success_rate': round(
                    (status_counts['completed'] / max(1, sum(status_counts.values()))) * 100, 2
                ),
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting task statistics: {e}")
            return {
                'error': str(e),
                'period_hours': hours,
                'generated_at': datetime.now().isoformat()
            }

    async def _auto_generate_faq(self, task: ChatTask, db: AsyncSession):
        """Auto-generate FAQ from completed chat task"""
        try:
            from app.models.faq import FAQ, FAQCategory
            import re
            import hashlib

            # Only create FAQ if response is good quality (has content and no errors)
            if not task.response_text or task.error_message:
                logger.debug(f"Skipping FAQ generation for task {task.task_id} - no response or has errors")
                return

            # Generate FAQ from task
            question = task.question
            answer = task.response_text[:5000]  # Limit answer length

            # Determine category based on deity
            category_mapping = {
                'guan_yin': FAQCategory.FORTUNE_READING,
                'guan_yu': FAQCategory.FORTUNE_READING,
                'mazu': FAQCategory.FORTUNE_READING,
                'yue_lao': FAQCategory.FORTUNE_READING,
                'asakusa': FAQCategory.FORTUNE_READING,
                'tianhou': FAQCategory.FORTUNE_READING,
                'zhusheng': FAQCategory.FORTUNE_READING,
                'erawan_shrine': FAQCategory.FORTUNE_READING
            }
            category = category_mapping.get(task.deity_id.lower(), FAQCategory.GENERAL)

            # Generate unique slug from question
            slug = re.sub(r'[^\w\s-]', '', question.lower())
            slug = re.sub(r'[-\s]+', '-', slug)[:200]

            # Make slug unique using hash
            content_hash = hashlib.md5(f"{question}{answer}".encode()).hexdigest()[:8]
            slug = f"{slug}-{content_hash}"

            # Ensure slug is unique
            base_slug = slug
            counter = 1
            while await db.scalar(select(FAQ).where(FAQ.slug == slug)):
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Create FAQ
            faq = FAQ(
                category=category,
                question=question,
                answer=answer,
                slug=slug,
                tags=f"{task.deity_id},fortune_reading,poem_{task.fortune_number}",
                display_order=0,
                is_published=False,  # Require admin approval before publishing
                created_by=task.user_id,
                view_count=0,
                helpful_votes=0
            )

            db.add(faq)
            await db.commit()

            logger.info(f"Auto-generated FAQ {faq.id} from task {task.task_id}")

        except Exception as e:
            logger.error(f"Error auto-generating FAQ from task {task.task_id}: {e}")
            # Don't raise - FAQ generation failure shouldn't break task completion


# Global instance
task_queue_service = TaskQueueService()
