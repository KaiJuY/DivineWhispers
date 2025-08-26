"""
Job model for tracking fortune-telling tasks
"""

import enum
from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, ForeignKey, Enum, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .transaction import Transaction
    from .job_result import JobResult


class JobStatus(enum.Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"  # Add for compatibility
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(enum.Enum):
    """Job type enumeration"""
    FORTUNE_DRAW = "fortune_draw"
    FORTUNE_INTERPRET = "fortune_interpret"
    GENERAL = "general"


class Job(BaseModel):
    """Job model for tracking fortune-telling tasks"""
    __tablename__ = "jobs"
    
    # Primary Key
    job_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="任務唯一 ID"
    )
    
    # Foreign Key to Users
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        comment="建立任務的使用者"
    )
    
    # Foreign Key to Transactions
    txn_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("transactions.txn_id", ondelete="RESTRICT"),
        nullable=False,
        comment="扣點交易"
    )
    
    # Job details
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False,
        comment="任務狀態"
    )
    
    input_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="任務輸入資料（檔案路徑 / URL）"
    )
    
    points_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="扣除點數數量"
    )
    
    # Task metadata
    job_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="任務類型（fortune, tarot, etc.）"
    )
    
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="任務優先級（數字越大優先級越高）"
    )
    
    # Expiration timestamp
    expire_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="任務結果保存期限"
    )
    
    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="錯誤訊息"
    )
    
    # Processing times
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="任務開始處理時間"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="任務完成時間"
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="jobs",
        lazy="select"
    )
    
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="job",
        lazy="select"
    )
    
    result: Mapped[Optional["JobResult"]] = relationship(
        "JobResult",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="select",
        uselist=False
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_jobs_user_id', 'user_id'),
        Index('idx_jobs_status', 'status'),
        Index('idx_jobs_txn_id', 'txn_id'),
        Index('idx_jobs_created_at', 'created_at'),
        Index('idx_jobs_expire_at', 'expire_at'),
        Index('idx_jobs_user_status', 'user_id', 'status'),
        Index('idx_jobs_priority_created', 'priority', 'created_at'),
    )
    
    def is_pending(self) -> bool:
        """Check if job is pending"""
        return self.status == JobStatus.PENDING
    
    def is_running(self) -> bool:
        """Check if job is running"""
        return self.status == JobStatus.RUNNING
    
    def is_completed(self) -> bool:
        """Check if job is completed"""
        return self.status == JobStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if job is failed"""
        return self.status == JobStatus.FAILED
    
    def can_be_started(self) -> bool:
        """Check if job can be started"""
        return self.status == JobStatus.PENDING
    
    def start_processing(self) -> None:
        """Mark job as started"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def mark_completed(self) -> None:
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
    
    def mark_failed(self, error_message: Optional[str] = None) -> None:
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        if error_message:
            self.error_message = error_message
    
    def is_expired(self) -> bool:
        """Check if job result has expired"""
        if not self.expire_at:
            return False
        return datetime.utcnow() > self.expire_at
    
    def get_processing_time(self) -> Optional[float]:
        """Get processing time in seconds"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None
    
    def __repr__(self) -> str:
        return (
            f"<Job(job_id={self.job_id}, user_id={self.user_id}, "
            f"status={self.status.value}, points_used={self.points_used})>"
        )