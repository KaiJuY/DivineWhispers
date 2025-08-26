"""
Simplified Fortune Job model for async task processing
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, Enum, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel
from .job import JobStatus, JobType


class FortuneJob(BaseModel):
    """Simplified job model for fortune processing tasks"""
    __tablename__ = "fortune_jobs"
    
    # Use string ID for UUID compatibility
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        comment="UUID job identifier"
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        comment="User who created the job"
    )
    
    job_type: Mapped[JobType] = mapped_column(
        Enum(JobType),
        nullable=False,
        comment="Type of fortune job"
    )
    
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False,
        comment="Current job status"
    )
    
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Job input data"
    )
    
    result_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Job result data"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="Error message if failed"
    )
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When processing started"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When job completed"
    )
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When job expires"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_fortune_jobs_user_id', 'user_id'),
        Index('idx_fortune_jobs_status', 'status'),
        Index('idx_fortune_jobs_type', 'job_type'),
        Index('idx_fortune_jobs_created_at', 'created_at'),
        Index('idx_fortune_jobs_user_status', 'user_id', 'status'),
    )
    
    def is_completed(self) -> bool:
        """Check if job is completed"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED]
    
    def is_processing(self) -> bool:
        """Check if job is being processed"""
        return self.status in [JobStatus.PROCESSING, JobStatus.RUNNING]
    
    def mark_started(self) -> None:
        """Mark job as started"""
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.utcnow()
    
    def mark_completed(self, result_data: Dict[str, Any]) -> None:
        """Mark job as completed with result"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result_data = result_data
    
    def mark_failed(self, error_message: str) -> None:
        """Mark job as failed with error"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message