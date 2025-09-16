"""
Task Queue Service for async chat processing
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.chat_task import ChatTask, TaskStatus
from app.services.poem_service import poem_service
from app.utils.deps import get_db
import uuid


logger = logging.getLogger(__name__)


class TaskQueueService:
    """Service for managing async task processing"""

    def __init__(self):
        self.active_tasks: Dict[str, ChatTask] = {}
        self.sse_connections: Dict[str, List] = {}  # task_id -> list of response objects
        self.is_processing = False

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
        """Start the background task processor"""
        if self.is_processing:
            return

        self.is_processing = True
        logger.info("Starting task queue processor")

        while self.is_processing:
            try:
                await self.process_queued_tasks()
                await asyncio.sleep(2)  # Check for new tasks every 2 seconds
            except Exception as e:
                logger.error(f"Error in task processor: {e}")
                await asyncio.sleep(5)  # Wait longer on error

    async def stop_processing(self):
        """Stop the background task processor"""
        self.is_processing = False
        logger.info("Stopping task queue processor")

    async def process_queued_tasks(self):
        """Process queued tasks"""
        # Get database session
        async for db in get_db():
            try:
                # Find queued tasks
                result = await db.execute(
                    select(ChatTask)
                    .where(ChatTask.status == TaskStatus.QUEUED)
                    .order_by(ChatTask.created_at)
                    .limit(5)  # Process up to 5 tasks at once
                )
                queued_tasks = result.scalars().all()

                # Process each task
                for task in queued_tasks:
                    if task.task_id not in self.active_tasks:
                        asyncio.create_task(self.process_task(task.task_id, db))

                break  # Exit the async generator
            except Exception as e:
                logger.error(f"Error getting queued tasks: {e}")

    async def process_task(self, task_id: str, db: AsyncSession):
        """Process a single task"""
        try:
            # Get task
            task = await self.get_task(task_id, db)
            if not task:
                logger.warning(f"Task {task_id} not found")
                return

            if task.status != TaskStatus.QUEUED:
                logger.warning(f"Task {task_id} is not queued (status: {task.status})")
                return

            self.active_tasks[task_id] = task
            start_time = time.time()

            logger.info(f"Processing task {task_id}: {task.question[:50]}...")

            # Update status to processing
            await self.update_task_progress(task, TaskStatus.PROCESSING, 10, "Starting analysis...", db)

            # Step 1: Analyze RAG context
            await self.update_task_progress(task, TaskStatus.ANALYZING_RAG, 30, "Analyzing fortune context...", db)
            await asyncio.sleep(1)  # Simulate RAG processing time

            # Get fortune data for context
            poem_data = await poem_service.get_poem_by_id(f"{task.deity_id}_{task.fortune_number}")
            if not poem_data:
                raise Exception(f"Fortune not found: {task.deity_id}_{task.fortune_number}")

            # Step 2: Generate LLM response
            await self.update_task_progress(task, TaskStatus.GENERATING_LLM, 70, "Consulting divine wisdom...", db)

            # Generate response using the poem service or mock
            response_text = await self.generate_response(task, poem_data)
            confidence = 75 + (hash(task.question) % 25)  # Mock confidence 75-99

            # Step 3: Complete
            await self.update_task_progress(task, TaskStatus.COMPLETED, 100, "Response generated successfully", db)

            # Set result
            task.set_result(
                response_text=response_text,
                confidence=confidence,
                sources_used=["RAG Analysis", "Traditional Interpretation", poem_data.temple]
            )

            # Save final result
            await db.commit()

            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"Completed task {task_id} in {processing_time}ms")

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

        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")

            # Update task with error
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.set_error(str(e))
                await db.commit()

                # Send error event to SSE clients
                await self.send_sse_event(task_id, {
                    "type": "error",
                    "error": str(e),
                    "retry_allowed": True
                })

        finally:
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

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
        """Generate AI response for the task"""
        # This would integrate with your LLM service
        # For now, using a mock response similar to the original

        await asyncio.sleep(2)  # Simulate processing time

        deity_name = {
            "yue_lao": "Yue Lao",
            "guan_yin": "Guan Yin",
            "mazu": "Mazu",
            "guan_yu": "Guan Yu"
        }.get(task.deity_id, task.deity_id.title())

        responses = [
            f'Regarding your question "{task.question}", the divine wisdom of {deity_name} through fortune #{task.fortune_number} suggests that patience and perseverance are your greatest allies. The ancient poem speaks of transformation and renewal - trust in the process and remain open to guidance.',

            f'Your inquiry "{task.question}" resonates deeply with the energy of fortune #{task.fortune_number}. The celestial signs indicate that positive changes are approaching. The poem\'s wisdom reminds us that every ending brings a new beginning.',

            f'The sacred wisdom of fortune #{task.fortune_number} illuminates your question: "{task.question}". Balance is essential in your current situation - neither force nor complete passivity, but mindful action guided by inner wisdom.',

            f'Through the lens of fortune #{task.fortune_number}, your question "{task.question}" reveals hidden opportunities. {deity_name} suggests focusing on what you can influence while releasing attachment to specific outcomes.',

            f'The divine teachings within fortune #{task.fortune_number} offer profound guidance for "{task.question}". Your intuition is particularly strong now - trust it to guide your decisions, as it is aligned with universal wisdom.'
        ]

        return responses[hash(task.question) % len(responses)]

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

        # Send to all connected clients
        for response_obj in self.sse_connections[task_id][:]:  # Copy list to avoid modification during iteration
            try:
                await response_obj.send(event_data)
            except Exception as e:
                logger.warning(f"Failed to send SSE event to client: {e}")
                self.remove_sse_connection(task_id, response_obj)


# Global instance
task_queue_service = TaskQueueService()