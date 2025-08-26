"""
JobResult model for storing fortune-telling task results
"""

from datetime import datetime
from sqlalchemy import BigInteger, String, Text, ForeignKey, DateTime, JSON, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    from .job import Job


class JobResult(Base):
    """JobResult model for storing task execution results"""
    __tablename__ = "job_results"
    
    # Primary Key
    result_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="結果唯一 ID"
    )
    
    # Foreign Key to Jobs
    job_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("jobs.job_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One result per job
        comment="對應任務"
    )
    
    # Result data
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="模型輸出結果（JSON格式）"
    )
    
    output_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="模型輸出結果（純文字格式）"
    )
    
    # File storage
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="存檔路徑或 URL"
    )
    
    file_size: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="檔案大小（bytes）"
    )
    
    file_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="檔案類型（MIME type）"
    )
    
    # Timestamps
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="完成時間"
    )
    
    retention_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="保留到期日（定期清理）"
    )
    
    # Result metadata
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="處理時間（秒）"
    )
    
    tokens_used: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="使用的 token 數量"
    )
    
    model_version: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="使用的模型版本"
    )
    
    # Quality metrics
    confidence_score: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="結果信心分數（0.0-1.0）"
    )
    
    # Relationships
    job: Mapped["Job"] = relationship(
        "Job",
        back_populates="result",
        lazy="select"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_job_results_job_id', 'job_id'),
        Index('idx_job_results_completed_at', 'completed_at'),
        Index('idx_job_results_retention_until', 'retention_until'),
        Index('idx_job_results_file_path', 'file_path'),
    )
    
    def has_output_data(self) -> bool:
        """Check if result has JSON output data"""
        return self.output_data is not None and len(self.output_data) > 0
    
    def has_output_text(self) -> bool:
        """Check if result has text output"""
        return self.output_text is not None and len(self.output_text.strip()) > 0
    
    def has_file(self) -> bool:
        """Check if result has associated file"""
        return self.file_path is not None and len(self.file_path.strip()) > 0
    
    def is_expired(self) -> bool:
        """Check if result has expired"""
        if not self.retention_until:
            return False
        return datetime.utcnow() > self.retention_until
    
    def get_file_size_mb(self) -> Optional[float]:
        """Get file size in MB"""
        if self.file_size:
            return self.file_size / (1024 * 1024)
        return None
    
    def get_primary_output(self) -> Optional[str]:
        """Get the primary output (prefer JSON, fallback to text)"""
        if self.has_output_data():
            # Try to get a readable summary from JSON
            if isinstance(self.output_data, dict):
                # Look for common keys that might contain the main result
                for key in ['result', 'output', 'fortune', 'interpretation', 'text']:
                    if key in self.output_data:
                        return str(self.output_data[key])
                # If no common keys found, return JSON string
                return str(self.output_data)
        
        if self.has_output_text():
            return self.output_text
        
        return None
    
    def set_retention_period(self, days: int) -> None:
        """Set retention period from now"""
        from datetime import timedelta
        self.retention_until = datetime.utcnow() + timedelta(days=days)
    
    def __repr__(self) -> str:
        return (
            f"<JobResult(result_id={self.result_id}, job_id={self.job_id}, "
            f"has_data={self.has_output_data()}, has_text={self.has_output_text()}, "
            f"has_file={self.has_file()})>"
        )