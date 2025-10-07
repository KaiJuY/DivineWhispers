"""
Async Chat API endpoints with task queue and SSE support
"""

import logging
from datetime import datetime
from typing import Optional, AsyncGenerator
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


# Database dependency
async def get_db_session():
    """Database session dependency for this module"""
    async for session in get_database_session():
        yield session

# API Endpoints

@router.post("/ask-question", response_model=TaskResponse)
async def ask_fortune_question(
    request: FortuneQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Submit a fortune question for async processing
    Returns task_id and SSE URL for progress tracking
    """
    try:
        # Validate deity
        if not deity_service.get_temple_name(request.deity_id):
            raise HTTPException(status_code=400, detail="Invalid deity ID")

        # Check if user already has an active task created in last 10 minutes (prevent spam)
        from app.models.chat_task import TaskStatus
        from sqlalchemy import select, or_
        from app.models.chat_task import ChatTask
        from datetime import datetime, timedelta

        # Only block if task was created in last 10 minutes (avoid stuck tasks blocking forever)
        ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)

        active_task_result = await db.execute(
            select(ChatTask).where(
                ChatTask.user_id == current_user.user_id,
                ChatTask.created_at >= ten_minutes_ago,
                or_(
                    ChatTask.status == TaskStatus.QUEUED,
                    ChatTask.status == TaskStatus.PROCESSING,
                    ChatTask.status == TaskStatus.ANALYZING_RAG,
                    ChatTask.status == TaskStatus.GENERATING_LLM
                )
            )
        )
        active_task = active_task_result.scalars().first()

        if active_task:
            raise HTTPException(
                status_code=409,
                detail="You already have a report being generated. Please wait for it to complete before requesting another."
            )

        # Check if user has enough balance (no deduction yet, just validation)
        from app.models.wallet import Wallet
        wallet_result = await db.execute(
            select(Wallet).where(Wallet.user_id == current_user.user_id)
        )
        wallet = wallet_result.scalar_one_or_none()

        if not wallet:
            raise HTTPException(status_code=400, detail="Wallet not found")

        if wallet.balance < 5:
            raise HTTPException(
                status_code=402,
                detail="Insufficient coins. You need 5 coins to generate a report."
            )

        # Create task (coins will be deducted when processing actually starts)
        task = await task_queue_service.create_task(
            user_id=current_user.user_id,
            deity_id=request.deity_id,
            fortune_number=request.fortune_number,
            question=request.question,
            context=request.context,
            db=db
        )

        logger.info(f"Created task {task.task_id} for user {current_user.user_id} (coins will be deducted when processing starts)")

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
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    SSE endpoint for real-time task progress updates
    """

    # Manual token authentication for SSE (matching deps.py pattern)
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
        # Verify token (same as get_current_user_token)
        payload = await verify_token_with_blacklist(db, auth_token, "access")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Convert user_id to int (same as get_current_user)
        try:
            user_id = int(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in token",
            )

        # Get user (same as get_current_user)
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
        logger.error(f"Authentication failed for SSE endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication failed: {str(e)}")

    # Verify task exists and belongs to user
    task = await task_queue_service.get_task(task_id, db)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    async def event_generator():
        import asyncio
        import json
        from app.core.database import get_async_session

        # Create a response object for SSE
        class SSEResponse:
            def __init__(self, generator_ref):
                self.closed = False
                self.generator_ref = generator_ref

            async def send(self, data):
                if not self.closed and self.generator_ref:
                    await self.generator_ref.put(data)

            def close(self):
                self.closed = True

        # Create an async queue for SSE events
        event_queue = asyncio.Queue()
        response_obj = SSEResponse(event_queue)

        try:
            # Add connection to task queue service
            task_queue_service.add_sse_connection(task_id, response_obj)

            # Initial prelude to defeat proxy/browser buffering
            yield ":" + (" " * 2048) + "\n\n"

            # Send initial status
            current_task = await task_queue_service.get_task(task_id, db)
            # Advise client on reconnection delay if needed
            yield f"retry setting: 2000\n\n"

            if current_task:
                # Extract status_code from status_message (format: "status_code:20")
                status_code = None
                if current_task.status_message and current_task.status_message.startswith("status_code:"):
                    try:
                        status_code = int(current_task.status_message.split(":")[1])
                    except (IndexError, ValueError):
                        pass

                initial_data = {
                    "type": "status",
                    "status": current_task.status.value,
                    "progress": current_task.progress,
                    "status_code": status_code
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
            ping_interval = 30  # Send ping every 30 seconds

            while not response_obj.closed and timeout_counter < max_timeout:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Wait for events from the queue with timeout
                    event_data = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                    yield event_data
                    timeout_counter = 0  # Reset timeout on activity

                    # Check if this is a completion event
                    try:
                        event_json = json.loads(event_data.replace("data: ", "").strip())
                        if event_json.get("type") in ["complete", "error"]:
                            # Add delay to ensure client receives the completion event before connection closes
                            await asyncio.sleep(0.5)
                            break
                    except (json.JSONDecodeError, AttributeError):
                        pass

                except asyncio.TimeoutError:
                    # No events received, increment timeout and send ping if needed
                    timeout_counter += 1

                    if timeout_counter % ping_interval == 0:  # Every 30 seconds
                        yield f"data: {json.dumps({'type': 'ping'})}\n\n"

                    # Check if task is completed (fallback) with short-lived DB session
                    async with get_async_session() as _db:
                        current_task = await task_queue_service.get_task(task_id, _db)
                    if current_task and current_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                        # Send final event if not already sent
                        if current_task.status == TaskStatus.COMPLETED:
                            final_data = {
                                "type": "complete",
                                "result": {
                                    "response": current_task.response_text,
                                    "confidence": current_task.confidence,
                                    "sources_used": current_task.sources_used,
                                    "processing_time_ms": current_task.processing_time_ms,
                                    "can_generate_report": current_task.can_generate_report == "true"
                                }
                            }
                            yield f"data: {json.dumps(final_data)}\n\n"
                        else:  # FAILED
                            error_data = {
                                "type": "error",
                                "error": current_task.error_message,
                                "retry_allowed": True
                            }
                            yield f"data: {json.dumps(error_data)}\n\n"
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
        media_type="text/event-stream; charset=utf-8",
        headers={
            # Prevent proxy buffering (e.g., Nginx) so events flush immediately
            "X-Accel-Buffering": "no",
            # Stronger no-cache to avoid intermediary caching/buffering
            "Cache-Control": "no-cache, no-store, must-revalidate, no-transform",
            "Pragma": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
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
    db: AsyncSession = Depends(get_db_session)
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


@router.get("/metrics")
async def get_service_metrics(
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get comprehensive service metrics (requires authentication)
    """
    try:
        # Get real-time metrics
        service_metrics = task_queue_service.get_service_metrics()

        # Get historical statistics
        task_statistics = await task_queue_service.get_task_statistics(db, hours)

        # Get circuit breaker status
        from app.utils.timeout_utils import (
            rag_circuit_breaker, llm_circuit_breaker, chromadb_circuit_breaker
        )

        circuit_breakers = {
            "rag_circuit_breaker": {
                "state": rag_circuit_breaker.state,
                "failure_count": rag_circuit_breaker.failure_count,
                "failure_threshold": rag_circuit_breaker.failure_threshold,
                "recovery_timeout": rag_circuit_breaker.recovery_timeout
            },
            "llm_circuit_breaker": {
                "state": llm_circuit_breaker.state,
                "failure_count": llm_circuit_breaker.failure_count,
                "failure_threshold": llm_circuit_breaker.failure_threshold,
                "recovery_timeout": llm_circuit_breaker.recovery_timeout
            },
            "chromadb_circuit_breaker": {
                "state": chromadb_circuit_breaker.state,
                "failure_count": chromadb_circuit_breaker.failure_count,
                "failure_threshold": chromadb_circuit_breaker.failure_threshold,
                "recovery_timeout": chromadb_circuit_breaker.recovery_timeout
            }
        }

        return {
            "service_metrics": service_metrics,
            "task_statistics": task_statistics,
            "circuit_breakers": circuit_breakers,
            "user_id": current_user.user_id,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting service metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get service metrics")


@router.get("/health")
async def service_health_check():
    """
    Public health check endpoint for the async chat service
    """
    try:
        # Check if task queue service is running
        is_healthy = task_queue_service.is_processing

        # Get basic worker pool status
        pool_metrics = task_queue_service.worker_pool.get_metrics()
        active_workers = pool_metrics['pool_status']['active_workers']
        total_workers = pool_metrics['pool_status']['max_workers']

        # Check circuit breaker states
        from app.utils.timeout_utils import (
            rag_circuit_breaker, llm_circuit_breaker, chromadb_circuit_breaker
        )

        circuit_breakers_healthy = all([
            cb.state != "OPEN" for cb in [
                rag_circuit_breaker, llm_circuit_breaker, chromadb_circuit_breaker
            ]
        ])

        overall_status = "healthy" if (is_healthy and circuit_breakers_healthy) else "degraded"

        return {
            "status": overall_status,
            "service": "async-chat",
            "task_queue_running": is_healthy,
            "active_workers": active_workers,
            "total_workers": total_workers,
            "circuit_breakers_healthy": circuit_breakers_healthy,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "service": "async-chat",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
