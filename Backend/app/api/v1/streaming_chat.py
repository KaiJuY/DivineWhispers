"""
Enhanced streaming chat endpoints with real-time progress
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.utils.deps import get_current_user
from app.core.database import get_database_session
from app.models.user import User
from app.models.chat_task import ChatTask, TaskStatus
from app.services.task_queue_service import task_queue_service
from app.services.deity_service import deity_service
from app.utils.progress_tracker import progress_manager, ProgressUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/streaming-chat", tags=["Streaming Chat"])


# Request/Response Models
class EnhancedFortuneRequest(BaseModel):
    """Enhanced request with streaming options"""
    deity_id: str = Field(..., description="Deity identifier")
    fortune_number: int = Field(..., ge=1, le=100, description="Fortune number")
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    context: Optional[dict] = Field(None, description="Additional context")
    enable_streaming: bool = Field(True, description="Enable real-time streaming updates")
    language: str = Field("zh", description="Response language")


class StreamingTaskResponse(BaseModel):
    """Response for streaming task"""
    task_id: str
    sse_url: str
    enhanced_sse_url: str
    status: str
    message: str
    streaming_enabled: bool


# Database dependency
async def get_db_session():
    """Database session dependency for this module"""
    async for session in get_database_session():
        yield session


@router.post("/ask-question", response_model=StreamingTaskResponse)
async def ask_fortune_question_streaming(
    request: EnhancedFortuneRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Submit a fortune question with enhanced streaming capabilities
    """
    try:
        # Validate deity
        if not deity_service.get_temple_name(request.deity_id):
            raise HTTPException(status_code=400, detail="Invalid deity ID")

        # Create task with enhanced context
        enhanced_context = request.context or {}
        enhanced_context.update({
            "language": request.language,
            "streaming_enabled": request.enable_streaming,
            "streaming_version": "v2"
        })

        task = await task_queue_service.create_task(
            user_id=current_user.user_id,
            deity_id=request.deity_id,
            fortune_number=request.fortune_number,
            question=request.question,
            context=enhanced_context,
            db=db
        )

        logger.info(f"Created enhanced streaming task {task.task_id} for user {current_user.user_id}")

        return StreamingTaskResponse(
            task_id=task.task_id,
            sse_url=f"/api/v1/async-chat/sse/{task.task_id}",
            enhanced_sse_url=f"/api/v1/streaming-chat/sse/{task.task_id}",
            status="queued",
            message="Your question has been queued for enhanced streaming processing",
            streaming_enabled=request.enable_streaming
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating streaming task: {e}")
        raise HTTPException(status_code=500, detail="Failed to process streaming request")


@router.get("/sse/{task_id}")
async def enhanced_streaming_endpoint(
    task_id: str,
    request: Request,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Enhanced SSE endpoint with detailed real-time progress
    """
    # Manual token authentication (same as async_chat.py)
    from app.core.security import verify_token_with_blacklist
    from app.models.user import User
    from sqlalchemy import select

    # Get token from query parameter or Authorization header
    auth_token = token
    if not auth_token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            auth_token = auth_header.split(" ")[1]

    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify token
        payload = await verify_token_with_blacklist(db, auth_token, "access")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Convert user_id to int
        try:
            user_id = int(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in token",
            )

        # Get user
        result = await db.execute(select(User).where(User.user_id == user_id))
        current_user = result.scalar_one_or_none()

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if user is active
        if not current_user.is_active():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed for enhanced SSE endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication failed: {str(e)}")

    # Verify task exists and belongs to user
    task = await task_queue_service.get_task(task_id, db)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    async def enhanced_event_generator():
        """Enhanced event generator with detailed progress tracking"""
        import asyncio
        import json
        from app.core.database import get_async_session

        # Create event queue for enhanced SSE
        event_queue = asyncio.Queue()
        progress_updates_received = 0

        class EnhancedSSEResponse:
            def __init__(self, queue_ref):
                self.closed = False
                self.queue_ref = queue_ref

            async def send(self, data):
                if not self.closed and self.queue_ref:
                    await self.queue_ref.put(data)

            def close(self):
                self.closed = True

        response_obj = EnhancedSSEResponse(event_queue)

        try:
            # Add connection to task queue service
            task_queue_service.add_sse_connection(task_id, response_obj)

            # Initial prelude to defeat proxy/browser buffering
            yield ":" + (" " * 2048) + "\n\n"

            # Check if we have a progress tracker for this task
            progress_tracker = progress_manager.get_tracker(task_id)
            if progress_tracker:
                # Subscribe to progress updates
                async def progress_callback(update: ProgressUpdate):
                    nonlocal progress_updates_received
                    progress_updates_received += 1

                    enhanced_data = {
                        "type": "enhanced_progress",
                        "task_id": update.task_id,
                        "stage": update.stage,
                        "progress": update.progress,
                        "message": update.message,
                        "data": update.data,
                        "timestamp": update.timestamp.isoformat(),
                        "update_number": progress_updates_received
                    }

                    if not response_obj.closed:
                        await response_obj.send(f"data: {json.dumps(enhanced_data)}\\n\\n")

                progress_tracker.subscribe(progress_callback)

            # Send initial status with enhanced info
            # Suggest client reconnection backoff and send initial status
            yield f"retry: 2000\n\n"

            current_task = await task_queue_service.get_task(task_id, db)
            if current_task:
                initial_data = {
                    "type": "enhanced_status",
                    "status": current_task.status.value,
                    "progress": current_task.progress,
                    "message": current_task.status_message,
                    "task_info": {
                        "deity_id": current_task.deity_id,
                        "fortune_number": current_task.fortune_number,
                        "question_preview": current_task.question[:50] + "..." if len(current_task.question) > 50 else current_task.question,
                        "created_at": current_task.created_at.isoformat(),
                        "streaming_enabled": current_task.context.get("streaming_enabled", False) if current_task.context else False
                    }
                }
                yield f"data: {json.dumps(initial_data)}\\n\\n"

                # If task is already completed, send result immediately
                if current_task.status == TaskStatus.COMPLETED:
                    result_data = {
                        "type": "enhanced_complete",
                        "result": {
                            "response": current_task.response_text,
                            "confidence": current_task.confidence,
                            "sources_used": current_task.sources_used,
                            "processing_time_ms": current_task.processing_time_ms,
                            "can_generate_report": current_task.can_generate_report == "true",
                            "progress_updates_count": progress_updates_received
                        },
                        "summary": {
                            "total_processing_time": current_task.processing_time_ms,
                            "stages_completed": ["processing", "analyzing_rag", "generating_llm", "completed"],
                            "final_status": "success"
                        }
                    }
                    yield f"data: {json.dumps(result_data)}\\n\\n"
                    return

                elif current_task.status == TaskStatus.FAILED:
                    error_data = {
                        "type": "enhanced_error",
                        "error": current_task.error_message,
                        "retry_allowed": True,
                        "debug_info": {
                            "progress_updates_received": progress_updates_received,
                            "failed_at": current_task.updated_at.isoformat() if current_task.updated_at else None
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\\n\\n"
                    return

            # Enhanced keep-alive and monitoring
            timeout_counter = 0
            max_timeout = 300  # 5 minutes
            ping_interval = 15   # Send ping every 15 seconds
            last_progress_update = datetime.now()

            while not response_obj.closed and timeout_counter < max_timeout:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Wait for events from the queue with timeout
                    event_data = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                    yield event_data
                    timeout_counter = 0  # Reset timeout on activity
                    last_progress_update = datetime.now()

                    # Check if this is a completion event
                    try:
                        event_json = json.loads(event_data.replace("data: ", "").strip())
                        if event_json.get("type") in ["enhanced_complete", "enhanced_error", "complete", "error"]:
                            # Send final summary
                            summary_data = {
                                "type": "session_summary",
                                "total_updates": progress_updates_received,
                                "session_duration_ms": int((datetime.now() - last_progress_update).total_seconds() * 1000),
                                "final_status": event_json.get("type"),
                                "timestamp": datetime.now().isoformat()
                            }
                            yield f"data: {json.dumps(summary_data)}\\n\\n"
                            break
                    except (json.JSONDecodeError, AttributeError):
                        pass

                except asyncio.TimeoutError:
                    # No events received, increment timeout and send enhanced ping
                    timeout_counter += 1

                    if timeout_counter % ping_interval == 0:  # Every 15 seconds
                        ping_data = {
                            "type": "enhanced_ping",
                            "timestamp": datetime.now().isoformat(),
                            "progress_updates_received": progress_updates_received,
                            "connection_alive_seconds": timeout_counter
                        }
                        yield f"data: {json.dumps(ping_data)}\\n\\n"

                    # Check if task is completed (fallback with enhanced info) using short-lived DB session
                    async with get_async_session() as _db:
                        current_task = await task_queue_service.get_task(task_id, _db)
                    if current_task and current_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                        # Send enhanced final event
                        if current_task.status == TaskStatus.COMPLETED:
                            final_data = {
                                "type": "enhanced_complete",
                                "result": {
                                    "response": current_task.response_text,
                                    "confidence": current_task.confidence,
                                    "sources_used": current_task.sources_used,
                                    "processing_time_ms": current_task.processing_time_ms,
                                    "can_generate_report": current_task.can_generate_report == "true",
                                    "progress_updates_count": progress_updates_received
                                },
                                "fallback_detection": True
                            }
                            yield f"data: {json.dumps(final_data)}\\n\\n"
                        else:  # FAILED
                            error_data = {
                                "type": "enhanced_error",
                                "error": current_task.error_message,
                                "retry_allowed": True,
                                "fallback_detection": True,
                                "debug_info": {
                                    "progress_updates_received": progress_updates_received
                                }
                            }
                            yield f"data: {json.dumps(error_data)}\\n\\n"
                        break

        except Exception as e:
            logger.error(f"Enhanced SSE error for task {task_id}: {e}")
            error_data = {
                "type": "enhanced_error",
                "error": "Enhanced connection error",
                "retry_allowed": True,
                "debug_info": {
                    "error_message": str(e),
                    "progress_updates_received": progress_updates_received
                }
            }
            yield f"data: {json.dumps(error_data)}\\n\\n"

        finally:
            # Clean up connection
            response_obj.close()
            task_queue_service.remove_sse_connection(task_id, response_obj)
            logger.info(f"Enhanced SSE connection closed for task {task_id} (received {progress_updates_received} progress updates)")

    return StreamingResponse(
        enhanced_event_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            # Prevent proxy buffering (e.g., Nginx) so events flush immediately
            "X-Accel-Buffering": "no",
            # Stronger no-cache to avoid intermediary caching/buffering
            "Cache-Control": "no-cache, no-store, must-revalidate, no-transform",
            "Pragma": "no-cache",
            "Connection": "keep-alive",
            "X-Streaming-Version": "v2-enhanced"
        }
    )


@router.get("/progress/{task_id}")
async def get_detailed_progress(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get detailed progress information for a task
    """
    try:
        # Verify task ownership
        task = await task_queue_service.get_task(task_id, db)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get progress tracker if exists
        progress_tracker = progress_manager.get_tracker(task_id)

        progress_info = {
            "task_id": task_id,
            "current_status": task.status.value,
            "current_progress": task.progress,
            "status_message": task.status_message,
            "created_at": task.created_at.isoformat(),
            "tracker_active": progress_tracker is not None
        }

        if progress_tracker:
            progress_info.update({
                "tracker_info": {
                    "current_stage": progress_tracker.current_stage,
                    "current_progress": progress_tracker.current_progress,
                    "elapsed_time_seconds": progress_tracker.get_elapsed_time(),
                    "subscribers_count": len(progress_tracker.subscribers)
                }
            })

        return progress_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting detailed progress for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get progress information")
