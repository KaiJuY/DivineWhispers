"""
Background Job Processor for Fortune Services
Handles async processing of fortune drawing and interpretation tasks
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.core.database import get_async_session
from app.models.fortune_job import FortuneJob, JobStatus, JobType
from app.schemas.fortune import FortuneDrawRequest, FortuneInterpretRequest
from app.services.poem_service import poem_service
from app.utils.websocket import websocket_manager


logger = logging.getLogger(__name__)


class JobProcessor:
    """Background job processor for fortune services"""
    
    def __init__(self):
        self.running = False
        self.worker_tasks = []
        self.max_concurrent_jobs = 2  # Reduced from 5 to 2 to decrease polling frequency
        self.poll_counter = 0  # Counter for periodic logging
        
    async def start_processing(self):
        """Start background job processing workers"""
        if self.running:
            logger.warning("Job processor is already running")
            return
            
        self.running = True
        logger.info("Starting job processor...")
        
        # Start worker tasks
        for i in range(self.max_concurrent_jobs):
            task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.worker_tasks.append(task)
            
        logger.info(f"Started {len(self.worker_tasks)} job processing workers")
    
    async def stop_processing(self):
        """Stop background job processing"""
        if not self.running:
            return
            
        logger.info("Stopping job processor...")
        self.running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
            
        # Wait for tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            
        self.worker_tasks.clear()
        logger.info("Job processor stopped")
    
    async def create_fortune_draw_job(
        self,
        user_id: str,
        request: FortuneDrawRequest,
        points_charged: int
    ) -> str:
        """
        Create a fortune draw job
        
        Args:
            user_id: User ID
            request: Fortune draw request
            points_charged: Points deducted from user
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        
        async with get_async_session() as db:
            job = FortuneJob(
                id=job_id,
                user_id=user_id,
                job_type=JobType.FORTUNE_DRAW,
                status=JobStatus.PENDING,
                payload={
                    "request": request.dict(),
                    "points_charged": points_charged
                },
                expires_at=datetime.utcnow() + timedelta(seconds=settings.FORTUNE_JOB_TIMEOUT_SECONDS)
            )
            
            db.add(job)
            await db.commit()
            
        logger.info(f"Created fortune draw job {job_id} for user {user_id}")
        return job_id
    
    async def create_fortune_interpret_job(
        self,
        user_id: str,
        poem_id: str,
        request: FortuneInterpretRequest,
        points_charged: int
    ) -> str:
        """
        Create a fortune interpretation job
        
        Args:
            user_id: User ID  
            poem_id: Poem ID to interpret
            request: Interpretation request
            points_charged: Points deducted from user
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        
        async with get_async_session() as db:
            job = FortuneJob(
                id=job_id,
                user_id=user_id,
                job_type=JobType.FORTUNE_INTERPRET,
                status=JobStatus.PENDING,
                payload={
                    "poem_id": poem_id,
                    "request": request.dict(),
                    "points_charged": points_charged
                },
                expires_at=datetime.utcnow() + timedelta(seconds=settings.FORTUNE_JOB_TIMEOUT_SECONDS)
            )
            
            db.add(job)
            await db.commit()
            
        logger.info(f"Created fortune interpret job {job_id} for user {user_id}")
        return job_id
    
    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status and result"""
        async with get_async_session() as db:
            query = select(FortuneJob).where(FortuneJob.id == job_id)
            result = await db.execute(query)
            job = result.scalar_one_or_none()
            
            if not job:
                return None
                
            return {
                "id": job.id,
                "status": job.status.value,
                "result_data": job.result_data,
                "error_message": job.error_message,
                "created_at": job.created_at,
                "completed_at": job.completed_at
            }
    
    async def get_user_jobs(
        self, 
        user_id: str, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[Dict]:
        """Get jobs for a user"""
        async with get_async_session() as db:
            query = (
                select(FortuneJob)
                .where(FortuneJob.user_id == user_id)
                .order_by(FortuneJob.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            
            result = await db.execute(query)
            jobs = result.scalars().all()
            
            return [
                {
                    "id": job.id,
                    "job_type": job.job_type.value,
                    "status": job.status.value,
                    "created_at": job.created_at,
                    "completed_at": job.completed_at,
                    "has_result": bool(job.result_data),
                    "result_data": job.result_data
                }
                for job in jobs
            ]
    
    async def _worker_loop(self, worker_name: str):
        """Main worker loop for processing jobs"""
        logger.info(f"Job worker {worker_name} started")
        local_poll_counter = 0
        
        while self.running:
            try:
                # Get next pending job
                job = await self._get_next_pending_job()
                
                if job:
                    logger.info(f"Worker {worker_name} processing job {job.id}")
                    await self._process_job(job)
                else:
                    # No jobs available, wait before checking again
                    local_poll_counter += 1
                    # Only log every 30 polls (5 minutes with 10s interval)
                    if local_poll_counter % 30 == 0:
                        logger.debug(f"Worker {worker_name} checked for jobs, none available")
                    await asyncio.sleep(10)  # Increased from 2 to 10 seconds
                    
            except Exception as e:
                logger.error(f"Error in worker {worker_name}: {e}")
                await asyncio.sleep(5)  # Wait before retrying
                
        logger.info(f"Job worker {worker_name} stopped")
    
    async def _get_next_pending_job(self) -> Optional[FortuneJob]:
        """Get next pending job from database"""
        async with get_async_session() as db:
            query = (
                select(FortuneJob)
                .where(FortuneJob.status == JobStatus.PENDING)
                .where(FortuneJob.expires_at > datetime.utcnow())
                .order_by(FortuneJob.created_at.asc())
                .limit(1)
            )
            
            result = await db.execute(query)
            job = result.scalar_one_or_none()
            
            if job:
                # Mark as processing to avoid double processing
                job.mark_started()
                await db.commit()

            return job
    
    async def _process_job(self, job: FortuneJob):
        """Process a specific job"""
        try:
            if job.job_type == JobType.FORTUNE_DRAW:
                await self._process_fortune_draw(job)
            elif job.job_type == JobType.FORTUNE_INTERPRET:
                await self._process_fortune_interpret(job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
                
        except Exception as e:
            logger.error(f"Error processing job {job.id}: {e}")
            await self._mark_job_failed(job.id, str(e))
    
    async def _process_fortune_draw(self, job: FortuneJob):
        """Process fortune drawing job"""
        payload = job.payload or {}
        request_data = payload.get("request", {})
        
        # Convert dict to FortuneDrawRequest
        draw_request = FortuneDrawRequest(**request_data)
        
        try:
            # Get random poem
            poem_data = await poem_service.get_random_poem(
                temple_preference=draw_request.temple_preference
            )
            
            # Generate interpretation
            question = draw_request.question or "What guidance can you offer me today?"
            interpretation_result = await poem_service.generate_fortune_interpretation(
                poem_data=poem_data,
                question=question,
                language=draw_request.language
            )
            
            # Prepare result
            result_data = {
                "type": "fortune_draw",
                "poem": poem_data.dict(),
                "interpretation": interpretation_result.dict(),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Mark job completed
            await self._mark_job_completed(job.id, result_data)
            
            # Send WebSocket notification
            await self._notify_user(job.user_id, {
                "type": "job_completed",
                "job_id": job.id,
                "job_type": "fortune_draw",
                "message": "Your fortune reading is ready!"
            })
            
            logger.info(f"Completed fortune draw job {job.id}")
            
        except Exception as e:
            logger.error(f"Error in fortune draw processing: {e}")
            raise
    
    async def _process_fortune_interpret(self, job: FortuneJob):
        """Process fortune interpretation job"""
        payload = job.payload or {}
        poem_id = payload.get("poem_id")
        request_data = payload.get("request", {})
        
        # Convert dict to FortuneInterpretRequest
        interpret_request = FortuneInterpretRequest(**request_data)
        
        try:
            # Get poem data
            poem_data = await poem_service.get_poem_by_id(poem_id)
            
            if not poem_data:
                raise ValueError(f"Poem {poem_id} not found")
            
            # Generate interpretation
            interpretation_result = await poem_service.generate_fortune_interpretation(
                poem_data=poem_data,
                question=interpret_request.question,
                language=interpret_request.language,
                user_context=interpret_request.additional_context
            )
            
            # Prepare result
            result_data = {
                "type": "fortune_interpret",
                "poem": poem_data.dict(),
                "interpretation": interpretation_result.dict(),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Mark job completed
            await self._mark_job_completed(job.id, result_data)
            
            # Send WebSocket notification
            await self._notify_user(job.user_id, {
                "type": "job_completed",
                "job_id": job.id,
                "job_type": "fortune_interpret",
                "message": "Your personalized interpretation is ready!"
            })
            
            logger.info(f"Completed fortune interpret job {job.id}")
            
        except Exception as e:
            logger.error(f"Error in fortune interpret processing: {e}")
            raise
    
    async def _mark_job_completed(self, job_id: str, result_data: Dict):
        """Mark job as completed with result data"""
        async with get_async_session() as db:
            query = (
                update(FortuneJob)
                .where(FortuneJob.id == job_id)
                .values(
                    status=JobStatus.COMPLETED,
                    result_data=result_data,
                    completed_at=datetime.utcnow()
                )
            )
            
            await db.execute(query)
            await db.commit()
    
    async def _mark_job_failed(self, job_id: str, error_message: str):
        """Mark job as failed with error message"""
        async with get_async_session() as db:
            query = (
                update(FortuneJob)
                .where(FortuneJob.id == job_id)
                .values(
                    status=JobStatus.FAILED,
                    error_message=error_message,
                    completed_at=datetime.utcnow()
                )
            )
            
            await db.execute(query)
            await db.commit()
    
    async def _notify_user(self, user_id: str, message: Dict):
        """Send WebSocket notification to user"""
        try:
            await websocket_manager.send_personal_message(
                message=message,
                user_id=user_id
            )
        except Exception as e:
            logger.warning(f"Failed to send WebSocket notification to user {user_id}: {e}")
    
    async def cleanup_expired_jobs(self):
        """Clean up expired jobs"""
        try:
            async with get_async_session() as db:
                # Mark expired jobs as failed
                query = (
                    update(FortuneJob)
                    .where(FortuneJob.expires_at < datetime.utcnow())
                    .where(FortuneJob.status.in_([JobStatus.PENDING, JobStatus.PROCESSING]))
                    .values(
                        status=JobStatus.FAILED,
                        error_message="Job expired",
                        completed_at=datetime.utcnow()
                    )
                )
                
                result = await db.execute(query)
                await db.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Cleaned up {result.rowcount} expired jobs")
                    
        except Exception as e:
            logger.error(f"Error cleaning up expired jobs: {e}")


# Global job processor instance
job_processor = JobProcessor()


async def start_job_processor():
    """Start the global job processor"""
    await job_processor.start_processing()


async def stop_job_processor():
    """Stop the global job processor"""
    await job_processor.stop_processing()


async def cleanup_jobs():
    """Cleanup expired jobs periodically"""
    while True:
        try:
            await job_processor.cleanup_expired_jobs()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error(f"Error in job cleanup: {e}")
            await asyncio.sleep(600)  # Retry in 10 minutes