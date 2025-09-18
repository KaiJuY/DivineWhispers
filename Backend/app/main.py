"""
Divine Whispers Backend - FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
import os

from app.core.config import settings
from app.core.database import engine, create_tables
from app.utils.websocket import websocket_manager
from app.utils.logging_config import setup_logging, get_logger

# Configure logging
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR,
    max_bytes=settings.LOG_MAX_BYTES,
    backup_count=settings.LOG_BACKUP_COUNT
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Divine Whispers Backend...")
    await create_tables()
    logger.info("Database tables created/verified")
    
    # Initialize fortune service and job processor
    try:
        from app.services.poem_service import poem_service
        from app.services.job_processor import job_processor, cleanup_jobs
        from app.services.task_queue_service import task_queue_service
        import asyncio

        # Initialize poem service
        poem_init_success = await poem_service.initialize_system()
        if poem_init_success:
            logger.info("Poem service initialized successfully")
        else:
            logger.warning("Poem service initialization failed - some features may be unavailable")

        # Start job processor
        await job_processor.start_processing()
        logger.info("Job processor started")

        # Start task queue service
        asyncio.create_task(task_queue_service.start_processing())
        logger.info("Task queue service started")

        # Start cleanup task
        cleanup_task = asyncio.create_task(cleanup_jobs())
        logger.info("Job cleanup task started")

    except Exception as e:
        logger.error(f"Error initializing services: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Divine Whispers Backend...")
    
    # Stop services
    try:
        from app.services.job_processor import job_processor
        from app.services.task_queue_service import task_queue_service
        await job_processor.stop_processing()
        await task_queue_service.stop_processing()
        logger.info("Services stopped")
    except Exception as e:
        logger.error(f"Error stopping services: {e}")
    
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title="Divine Whispers API",
    description="Fortune-telling application backend with ChromaDB integration",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
asset_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Asset")
if os.path.exists(asset_dir):
    app.mount("/images", StaticFiles(directory=asset_dir), name="images")
    app.mount("/static", StaticFiles(directory=asset_dir), name="static")
    logger.info(f"Static files mounted from: {asset_dir}")
else:
    logger.warning(f"Asset directory not found: {asset_dir}")


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_exception"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "internal_error"
            }
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Divine Whispers Backend",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Divine Whispers API",
        "docs": "/api/docs",
        "health": "/health"
    }


# WebSocket endpoint for real-time notifications and chat
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket, user_id: str):
    """WebSocket endpoint for real-time user notifications and chat"""
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                # Parse incoming message
                import json
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                if message_type == "chat_message":
                    # Handle incoming chat message
                    from app.services.chat_service import chat_service
                    from app.models.chat_message import MessageType
                    from app.schemas.chat import ChatMessageCreate
                    from app.core.database import get_async_session

                    # Get database session
                    async with get_async_session() as db:
                        try:
                            session_id = message.get("session_id")
                            content = message.get("content", "")
                            
                            if session_id and content:
                                # Send typing indicator
                                await websocket_manager.send_chat_typing_indicator(
                                    user_id, session_id, True
                                )
                                
                                # Generate streaming response
                                full_response = ""
                                async for chunk in chat_service.generate_fortune_response(
                                    session_id=session_id,
                                    user_message=content,
                                    user_id=int(user_id),
                                    db=db
                                ):
                                    full_response += chunk + " "
                                    await websocket_manager.send_chat_response_stream(
                                        user_id, session_id, chunk, False
                                    )
                                
                                # Send completion signal
                                await websocket_manager.send_chat_response_stream(
                                    user_id, session_id, "", True
                                )
                                
                                # Save assistant response to database
                                assistant_message_data = ChatMessageCreate(
                                    content=full_response.strip(),
                                    metadata={"generated_via": "websocket"}
                                )
                                
                                await chat_service.add_message(
                                    session_id=session_id,
                                    user_id=int(user_id),
                                    message_data=assistant_message_data,
                                    message_type=MessageType.ASSISTANT,
                                    db=db
                                )
                                
                                # Turn off typing indicator
                                await websocket_manager.send_chat_typing_indicator(
                                    user_id, session_id, False
                                )
                                
                        except Exception as e:
                            logger.error(f"Error processing chat message: {e}")
                            await websocket_manager.send_error_notification(
                                user_id, "Failed to process your message"
                            )
                
                elif message_type == "ping":
                    # Handle ping/pong for connection health
                    await websocket_manager.send_personal_message(
                        {"type": "pong", "timestamp": data.get("timestamp")}, user_id
                    )
                
                else:
                    # Echo back for other message types
                    await websocket_manager.send_personal_message(
                        f"Message received: {data}", user_id
                    )
                    
            except json.JSONDecodeError:
                # Handle non-JSON messages (legacy support)
                await websocket_manager.send_personal_message(
                    f"Message received: {data}", user_id
                )
                
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
    finally:
        websocket_manager.disconnect(user_id)


# Include API routers
from app.api.v1 import auth, admin, fortune, wallet, deities, chat, contact, async_chat
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administration"])
app.include_router(fortune.router, prefix="/api/v1", tags=["Fortune"])
app.include_router(wallet.router, prefix="/api/v1", tags=["Wallet"])
app.include_router(deities.router, prefix="/api/v1", tags=["Deities"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(contact.router, prefix="/api/v1", tags=["Contact"])
app.include_router(async_chat.router, prefix="/api/v1", tags=["Async Chat"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )