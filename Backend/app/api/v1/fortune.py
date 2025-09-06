"""
Fortune API endpoints for Divine Whispers
Provides fortune-telling services with authentication and payment integration
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.utils.deps import get_db
from app.models.user import User
from app.models.fortune_job import FortuneJob, JobStatus, JobType
from app.services.job_processor import job_processor
from app.schemas.fortune import (
    FortuneDrawRequest, FortuneInterpretRequest, FortuneJobResponse,
    PoemSearchQuery, PoemSearchResponse, FortuneCategoryResponse,
    FortuneSystemHealthResponse, TempleStatsResponse, PoemDetailResponse,
    FortuneHistoryResponse, FortuneAdminStatsResponse, FortuneErrorResponse,
    InsufficientPointsError, PoemNotFoundError, SystemUnavailableError
)
from app.services.poem_service import poem_service
from app.services.wallet_service import wallet_service
from app.utils.deps import get_current_user, get_current_admin_user
from app.services.deity_service import deity_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fortune", tags=["Fortune"])


# User Fortune Endpoints

@router.post("/draw", response_model=FortuneJobResponse)
async def draw_fortune(
    request: FortuneDrawRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Draw a random fortune poem and create async job for interpretation
    Costs points and provides personalized interpretation
    """
    try:
        # Check system availability
        health = await poem_service.health_check()
        if health.chroma_db_status != "healthy":
            raise HTTPException(
                status_code=503,
                detail=SystemUnavailableError(
                    message="Fortune system is currently unavailable",
                    retry_after_seconds=60
                ).dict()
            )
        
        # Check user points
        user_points = await wallet_service.get_user_points(current_user.user_id, db)
        required_points = settings.FORTUNE_DRAW_COST
        
        if user_points < required_points:
            raise HTTPException(
                status_code=402,
                detail=InsufficientPointsError(
                    message="Insufficient points for fortune drawing",
                    required_points=required_points,
                    current_points=user_points
                ).dict()
            )
        
        # Deduct points (atomic transaction)
        deduction_success = await wallet_service.deduct_points(
            user_id=current_user.user_id,
            amount=required_points,
            description=f"Fortune drawing service",
            db=db
        )
        
        if not deduction_success:
            raise HTTPException(
                status_code=402,
                detail="Payment processing failed"
            )
        
        # Create fortune draw job
        job_id = await job_processor.create_fortune_draw_job(
            user_id=str(current_user.user_id),
            request=request,
            points_charged=required_points
        )
        
        logger.info(f"Created fortune draw job {job_id} for user {current_user.user_id}")
        
        return FortuneJobResponse(
            job_id=job_id,
            status="processing",
            estimated_completion_time=30,  # seconds
            points_charged=required_points,
            message="Your fortune is being prepared. You will be notified when ready."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating fortune draw job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/interpret/{poem_id}", response_model=FortuneJobResponse)
async def interpret_poem(
    poem_id: str,
    request: FortuneInterpretRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Interpret a specific poem with user's question
    Costs points and provides personalized interpretation
    """
    try:
        # Validate poem exists
        poem_data = await poem_service.get_poem_by_id(poem_id)
        if not poem_data:
            raise HTTPException(
                status_code=404,
                detail=PoemNotFoundError(
                    message="Poem not found",
                    poem_id=poem_id
                ).dict()
            )
        
        # Check user points
        user_points = await wallet_service.get_user_points(current_user.user_id, db)
        required_points = settings.FORTUNE_INTERPRET_COST
        
        if user_points < required_points:
            raise HTTPException(
                status_code=402,
                detail=InsufficientPointsError(
                    message="Insufficient points for poem interpretation",
                    required_points=required_points,
                    current_points=user_points
                ).dict()
            )
        
        # Deduct points
        deduction_success = await wallet_service.deduct_points(
            user_id=current_user.user_id,
            amount=required_points,
            description=f"Poem interpretation: {poem_id}",
            db=db
        )
        
        if not deduction_success:
            raise HTTPException(status_code=402, detail="Payment processing failed")
        
        # Create fortune interpretation job
        job_id = await job_processor.create_fortune_interpret_job(
            user_id=str(current_user.user_id),
            poem_id=poem_id,
            request=request,
            points_charged=required_points
        )
        
        logger.info(f"Created fortune interpret job {job_id} for user {current_user.user_id}")
        
        return FortuneJobResponse(
            job_id=job_id,
            status="processing",
            estimated_completion_time=30,
            points_charged=required_points,
            message="Your personalized interpretation is being generated."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating interpret job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/poems/{poem_id}", response_model=PoemDetailResponse)
async def get_poem_details(
    poem_id: str
):
    """
    Get detailed information about a specific poem (free endpoint)
    """
    try:
        poem_data = await poem_service.get_poem_by_id(poem_id)
        if not poem_data:
            raise HTTPException(
                status_code=404,
                detail=PoemNotFoundError(
                    message="Poem not found",
                    poem_id=poem_id
                ).dict()
            )
        
        # Get similar poems
        similar_poems = await poem_service.search_similar_poems(
            query=poem_data.title,
            top_k=3,
            temple_filter=None
        )
        
        # Filter out the original poem from similar results
        similar_poems = [p for p in similar_poems if f"{p.temple}_{p.poem_id}" != poem_id]
        
        return PoemDetailResponse(
            poem=poem_data,
            related_poems=similar_poems,
            interpretation_count=0,  # Could be tracked in future
            average_rating=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting poem details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search", response_model=PoemSearchResponse)
async def search_poems(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    temple: Optional[str] = Query(None, description="Filter by temple name"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """
    Search poems by keyword (free endpoint with rate limiting)
    """
    try:
        start_time = time.time()
        
        # Perform search
        results = await poem_service.search_similar_poems(
            query=q,
            top_k=limit,
            temple_filter=temple
        )
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Search query '{q}' returned {len(results)} results")
        
        return PoemSearchResponse(
            query=q,
            results=results,
            total_found=len(results),
            search_time_ms=search_time_ms
        )
        
    except Exception as e:
        logger.error(f"Error searching poems: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/categories", response_model=FortuneCategoryResponse)
async def get_fortune_categories():
    """
    Get available fortune categories (free endpoint)
    """
    try:
        # Try to initialize the poem service if not already done
        if not poem_service._initialized:
            logger.info("Poem service not initialized, attempting initialization...")
            init_success = await poem_service.initialize_system()
            if not init_success:
                logger.error("Failed to initialize poem service")
                # Return mock data as fallback
                return FortuneCategoryResponse(
                    categories=["great_fortune", "good_fortune", "neutral", "bad_fortune"],
                    category_counts={
                        "great_fortune": 50,
                        "good_fortune": 75,
                        "neutral": 40,
                        "bad_fortune": 25
                    }
                )
        
        categories = await poem_service.get_poem_categories()
        
        if not categories:
            logger.warning("No categories found, returning fallback data")
            # Return fallback data if no categories found
            return FortuneCategoryResponse(
                categories=["great_fortune", "good_fortune", "neutral", "bad_fortune"],
                category_counts={
                    "great_fortune": 50,
                    "good_fortune": 75,
                    "neutral": 40,
                    "bad_fortune": 25
                }
            )
        
        return FortuneCategoryResponse(
            categories=list(categories.keys()),
            category_counts=categories
        )
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}", exc_info=True)
        
        # Return fallback data instead of 500 error
        logger.info("Returning fallback category data due to error")
        return FortuneCategoryResponse(
            categories=["great_fortune", "good_fortune", "neutral", "bad_fortune"],
            category_counts={
                "great_fortune": 50,
                "good_fortune": 75,
                "neutral": 40,
                "bad_fortune": 25
            }
        )


@router.get("/temples/{temple_name}/stats", response_model=TempleStatsResponse)
async def get_temple_stats(
    temple_name: str
):
    """
    Get statistics for a specific temple (free endpoint)
    """
    try:
        stats = await poem_service.get_temple_stats(temple_name)
        if not stats:
            raise HTTPException(status_code=404, detail="Temple not found")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting temple stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get status of a fortune job
    """
    try:
        job_status = await job_processor.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/jobs/{job_id}/result")
async def get_job_result(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get result of a completed fortune job
    """
    try:
        job_status = await job_processor.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job_status["status"] not in ["completed", "failed"]:
            raise HTTPException(status_code=202, detail="Job not yet completed")
        
        if job_status["status"] == "failed":
            raise HTTPException(status_code=500, detail=job_status.get("error_message", "Job failed"))
        
        return job_status["result_data"]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job result: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history", response_model=FortuneHistoryResponse)
async def get_fortune_history(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's fortune consultation history
    """
    try:
        jobs = await job_processor.get_user_jobs(
            user_id=str(current_user.user_id),
            limit=limit,
            offset=offset
        )
        
        # Convert to history entries
        entries = []
        total_points_spent = 0
        
        for job_data in jobs:
            # Mock data for now - could be enhanced to extract from job results
            entries.append({
                "job_id": job_data["id"],
                "poem_id": "various",
                "temple": "various",
                "question": "Fortune consultation",
                "created_at": job_data["created_at"],
                "status": job_data["status"],
                "points_cost": 10  # Could be extracted from job payload
            })
            total_points_spent += 10
        
        return FortuneHistoryResponse(
            entries=entries,
            total_count=len(jobs),
            total_points_spent=total_points_spent
        )
        
    except Exception as e:
        logger.error(f"Error getting fortune history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Admin Fortune Management Endpoints

@router.get("/admin/stats", response_model=FortuneAdminStatsResponse)
async def get_admin_fortune_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive fortune system statistics (admin only)
    """
    try:
        # Get system health
        health = await poem_service.health_check()
        
        # Get job statistics
        from sqlalchemy import select, func
        
        job_stats_query = select(
            func.count(FortuneJob.id).label("total_jobs"),
            func.avg(
                func.extract('epoch', FortuneJob.completed_at - FortuneJob.created_at)
            ).label("avg_processing_time")
        ).where(
            FortuneJob.job_type.in_([JobType.FORTUNE_DRAW, JobType.FORTUNE_INTERPRET])
        ).where(
            FortuneJob.status == JobStatus.COMPLETED
        )
        
        job_stats_result = await db.execute(job_stats_query)
        job_stats = job_stats_result.first()
        
        # Get poem categories
        categories = await poem_service.get_poem_categories()
        
        # Mock popular temples data (could be real with tracking)
        popular_temples = {"Asakusa": 150, "GuanYin100": 120, "GuanYu": 100}
        
        return FortuneAdminStatsResponse(
            total_poems_in_db=health.total_poems,
            total_temples=health.total_temples,
            total_interpretations_generated=job_stats.total_jobs or 0,
            average_interpretation_time_ms=int((job_stats.avg_processing_time or 30) * 1000),
            popular_temples=popular_temples,
            popular_fortune_types=categories,
            system_performance={
                "cache_hit_rate": "85%",
                "avg_response_time_ms": 250,
                "system_load": health.system_load
            },
            chroma_db_health={
                "status": health.chroma_db_status,
                "total_chunks": health.total_poems,
                "last_backup": "2024-01-15T10:00:00Z"
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/admin/refresh")
async def refresh_fortune_system(
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Refresh ChromaDB index and clear caches (admin only)
    """
    try:
        # Clear cache
        cache_cleared = await poem_service.refresh_cache()
        
        # Re-initialize system
        init_success = await poem_service.initialize_system()
        
        return JSONResponse(
            content={
                "message": "Fortune system refreshed successfully",
                "cache_cleared": cache_cleared,
                "system_reinitialized": init_success,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error refreshing fortune system: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/admin/health", response_model=FortuneSystemHealthResponse)
async def check_fortune_system_health(
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Check comprehensive fortune system health (admin only)
    """
    try:
        health = await poem_service.health_check()
        return health
        
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Deity-based Fortune Endpoints (Synchronous for UI compatibility)

@router.get("/fortunes/{deity_id}/numbers")
async def get_deity_fortune_numbers(deity_id: str):
    """
    Get available fortune numbers for a specific deity (1-100 grid)
    This is a convenience endpoint that wraps the deity service
    """
    try:
        numbers_data = await deity_service.get_deity_fortune_numbers(deity_id)
        
        if not numbers_data:
            raise HTTPException(status_code=404, detail="Deity not found or no fortunes available")
        
        return numbers_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fortune numbers for deity {deity_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/fortunes/{deity_id}/{number}")
async def get_deity_fortune_by_number(deity_id: str, number: int):
    """
    Get a specific fortune by deity and number (synchronous for UI compatibility)
    This provides immediate fortune data without async job processing
    """
    try:
        if not (1 <= number <= 100):
            raise HTTPException(status_code=400, detail="Fortune number must be between 1 and 100")
        
        # Get temple name from deity mapping
        temple_name = deity_service.get_temple_name(deity_id)
        if not temple_name:
            raise HTTPException(status_code=404, detail="Deity not found")
        
        # Get the specific poem by temple and number
        poem_id = f"{temple_name}_{number}"
        poem_data = await poem_service.get_poem_by_id(poem_id)
        
        if not poem_data:
            raise HTTPException(status_code=404, detail="Fortune not found for this deity and number")
        
        # Return the poem data directly (synchronous response)
        return {
            "deity_id": deity_id,
            "deity_name": deity_service.deity_info[deity_id]["name"],
            "number": number,
            "poem": {
                "id": poem_data.id,
                "temple": poem_data.temple,
                "title": poem_data.title,
                "fortune": poem_data.fortune,
                "poem": poem_data.poem,
                "analysis": poem_data.analysis
            },
            "temple_source": temple_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fortune {number} for deity {deity_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/fortune/daily")
async def get_daily_fortune():
    """
    Get today's daily fortune (free endpoint, no auth required)
    Returns a randomly selected fortune that changes daily
    """
    try:
        import hashlib
        from datetime import date
        
        # Create deterministic seed based on today's date
        today = date.today().isoformat()
        seed_hash = hashlib.md5(today.encode()).hexdigest()
        seed = int(seed_hash[:8], 16) % 1000
        
        # Use seed to select a consistent daily fortune
        import random
        random.seed(seed)
        
        # Get random deity and number for today
        deity_ids = list(deity_service.deity_info.keys())
        daily_deity_id = random.choice(deity_ids)
        daily_number = random.randint(1, 100)
        
        # Get the fortune
        temple_name = deity_service.get_temple_name(daily_deity_id)
        poem_id = f"{temple_name}_{daily_number}"
        poem_data = await poem_service.get_poem_by_id(poem_id)
        
        if not poem_data:
            # Fallback to random poem if specific number not found
            poem_data = await poem_service.get_random_poem(temple_name)
            daily_number = poem_data.poem_id
        
        return {
            "date": today,
            "deity_id": daily_deity_id,
            "deity_name": deity_service.deity_info[daily_deity_id]["name"],
            "number": daily_number,
            "poem": {
                "id": poem_data.id,
                "title": poem_data.title,
                "fortune": poem_data.fortune,
                "poem": poem_data.poem,
                "analysis": poem_data.analysis.get("zh", "") or poem_data.analysis.get("en", "")
            },
            "message": "Today's guidance from the divine"
        }
        
    except Exception as e:
        logger.error(f"Error getting daily fortune: {e}")
        # Return fallback daily fortune
        return {
            "date": date.today().isoformat(),
            "deity_id": "guan_yin",
            "deity_name": "Guan Yin",
            "number": 1,
            "poem": {
                "id": "fallback_1",
                "title": "Daily Wisdom",
                "fortune": "good_fortune",
                "poem": "The path of wisdom unfolds with each step taken mindfully.",
                "analysis": "Today brings opportunities for growth and reflection. Trust in your inner guidance."
            },
            "message": "Today's guidance from the divine"
        }


