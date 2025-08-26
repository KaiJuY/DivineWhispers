"""
Divine Whispers Backend - FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging

from app.core.config import settings
from app.core.database import engine, create_tables
from app.utils.websocket import websocket_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        await job_processor.stop_processing()
        logger.info("Job processor stopped")
    except Exception as e:
        logger.error(f"Error stopping job processor: {e}")
    
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


# WebSocket endpoint for real-time notifications
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket, user_id: str):
    """WebSocket endpoint for real-time user notifications"""
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Echo back for testing (can be removed in production)
            await websocket_manager.send_personal_message(
                f"Message received: {data}", user_id
            )
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
    finally:
        websocket_manager.disconnect(user_id)


# Include API routers
from app.api.v1 import auth, admin, fortune, wallet
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administration"]) 
app.include_router(fortune.router, prefix="/api/v1", tags=["Fortune"])
app.include_router(wallet.router, prefix="/api/v1", tags=["Wallet"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )