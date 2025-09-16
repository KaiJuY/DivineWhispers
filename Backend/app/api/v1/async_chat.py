"""
Async Chat API endpoints with task queue and SSE support
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.utils.deps import get_db
from app.models.user import User
from app.models.chat_task import ChatTask, TaskStatus
from app.services.task_queue_service import task_queue_service
from app.utils.deps import get_current_user
from app.services.deity_service import deity_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/async-chat", tags=["Async Chat"])


# Request/Response Models
class FortuneQuestionRequest(BaseModel):
    """Request to ask a fortune question"""
    deity_id: str = Field(..., description="Deity identifier")
    fortune_number: int = Field(..., ge=1, le=100, description="Fortune number")
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    context: Optional[dict] = Field(None, description="Additional context")


class TaskResponse(BaseModel):
    """Response with task information"""
    task_id: str
    sse_url: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Task status response"""
    task_id: str
    status: str
    progress: int
    message: str
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: str
    processing_time_ms: Optional[int] = None


# API Endpoints

@router.post("/ask-question", response_model=TaskResponse)
async def ask_fortune_question(
    request: FortuneQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a fortune question for async processing
    Returns task_id and SSE URL for progress tracking
    """
    try:
        # Validate deity
        if not deity_service.get_temple_name(request.deity_id):
            raise HTTPException(status_code=400, detail="Invalid deity ID")

        # Create task
        task = await task_queue_service.create_task(
            user_id=current_user.user_id,
            deity_id=request.deity_id,
            fortune_number=request.fortune_number,
            question=request.question,
            context=request.context,
            db=db
        )

        logger.info(f"Created task {task.task_id} for user {current_user.user_id}")

        return TaskResponse(
            task_id=task.task_id,
            sse_url=f"/api/v1/async-chat/sse/{task.task_id}",
            status="queued",
            message="Your question has been queued for processing"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to process request")


@router.get("/sse/{task_id}")
async def stream_task_progress(
    task_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    SSE endpoint for real-time task progress updates
    """
    # Verify task exists and belongs to user
    task = await task_queue_service.get_task(task_id, db)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    async def event_generator():
        import asyncio
        import json

        # Create a response object for SSE
        class SSEResponse:
            def __init__(self):
                self.closed = False

            async def send(self, data):
                if not self.closed:
                    yield data

            def close(self):
                self.closed = True

        response_obj = SSEResponse()

        try:
            # Add connection to task queue service
            task_queue_service.add_sse_connection(task_id, response_obj)

            # Send initial status
            current_task = await task_queue_service.get_task(task_id, db)
            if current_task:
                initial_data = {
                    "type": "status",
                    "status": current_task.status.value,
                    "progress": current_task.progress,
                    "message": current_task.status_message
                }
                yield f"data: {json.dumps(initial_data)}\n\n"

                # If task is already completed, send result immediately
                if current_task.status == TaskStatus.COMPLETED:
                    result_data = {
                        "type": "complete",
                        "result": {
                            "response": current_task.response_text,
                            "confidence": current_task.confidence,
                            "sources_used": current_task.sources_used,
                            "processing_time_ms": current_task.processing_time_ms,
                            "can_generate_report": current_task.can_generate_report == "true"
                        }
                    }
                    yield f"data: {json.dumps(result_data)}\n\n"
                    return

                elif current_task.status == TaskStatus.FAILED:
                    error_data = {
                        "type": "error",
                        "error": current_task.error_message,
                        "retry_allowed": True
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    return

            # Keep connection alive and wait for updates
            timeout_counter = 0
            max_timeout = 300  # 5 minutes

            while not response_obj.closed and timeout_counter < max_timeout:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Send keepalive ping
                if timeout_counter % 30 == 0:  # Every 30 seconds
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"

                await asyncio.sleep(1)
                timeout_counter += 1

                # Check if task is completed
                current_task = await task_queue_service.get_task(task_id, db)
                if current_task and current_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    break

        except Exception as e:
            logger.error(f"SSE error for task {task_id}: {e}")
            error_data = {
                "type": "error",
                "error": "Connection error",
                "retry_allowed": True
            }
            yield f"data: {json.dumps(error_data)}\n\n"

        finally:
            # Clean up connection
            response_obj.close()
            task_queue_service.remove_sse_connection(task_id, response_obj)
            logger.info(f"SSE connection closed for task {task_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current status of a task (fallback for SSE)
    """
    try:
        task = await task_queue_service.get_task(task_id, db)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        result = None
        if task.status == TaskStatus.COMPLETED:
            result = {
                "response": task.response_text,
                "confidence": task.confidence,
                "sources_used": task.sources_used,
                "processing_time_ms": task.processing_time_ms,
                "can_generate_report": task.can_generate_report == "true"
            }

        return TaskStatusResponse(
            task_id=task.task_id,
            status=task.status.value,
            progress=task.progress,
            message=task.status_message,
            result=result,
            error=task.error_message,
            created_at=task.created_at.isoformat(),
            processing_time_ms=task.processing_time_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task status")


@router.get("/history")
async def get_user_chat_history(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's chat history
    """
    try:
        tasks = await task_queue_service.get_user_tasks(
            user_id=current_user.user_id,
            limit=limit,
            offset=offset,
            db=db
        )

        history = []
        for task in tasks:
            history.append({
                "task_id": task.task_id,
                "deity_id": task.deity_id,
                "fortune_number": task.fortune_number,
                "question": task.question,
                "status": task.status.value,
                "response": task.response_text if task.status == TaskStatus.COMPLETED else None,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            })

        return {
            "history": history,
            "total_count": len(history),
            "has_more": len(tasks) == limit
        }

    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")