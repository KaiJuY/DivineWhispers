"""
Chat Task Model for async fortune question processing
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Enum
from datetime import datetime
import enum
import uuid
from app.models.base import Base


class TaskStatus(enum.Enum):
    """Task processing status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    ANALYZING_RAG = "analyzing_rag"
    GENERATING_LLM = "generating_llm"
    COMPLETED = "completed"
    FAILED = "failed"


class ChatTask(Base):
    """Chat task model for async processing"""

    __tablename__ = "chat_tasks"

    task_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, nullable=False)

    # Request data
    deity_id = Column(String(50), nullable=False)
    fortune_number = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)

    # Task status
    status = Column(Enum(TaskStatus), default=TaskStatus.QUEUED, nullable=False)
    progress = Column(Integer, default=0)  # 0-100
    status_message = Column(String(255), default="Task queued")

    # Results
    response_text = Column(Text, nullable=True)
    confidence = Column(Integer, nullable=True)  # 0-100
    sources_used = Column(JSON, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Report generation
    can_generate_report = Column(String(10), default="true")  # "true"/"false" as string
    report_generated = Column(String(10), default="false")

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "deity_id": self.deity_id,
            "fortune_number": self.fortune_number,
            "question": self.question,
            "context": self.context,
            "status": self.status.value if self.status else None,
            "progress": self.progress,
            "status_message": self.status_message,
            "response_text": self.response_text,
            "confidence": self.confidence,
            "sources_used": self.sources_used,
            "processing_time_ms": self.processing_time_ms,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "can_generate_report": self.can_generate_report == "true",
            "report_generated": self.report_generated == "true"
        }

    def update_progress(self, status: TaskStatus, progress: int, message: str):
        """Update task progress"""
        self.status = status
        self.progress = progress
        self.status_message = message

        if status == TaskStatus.PROCESSING and self.started_at is None:
            self.started_at = datetime.utcnow()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            self.completed_at = datetime.utcnow()
            if self.started_at:
                delta = self.completed_at - self.started_at
                self.processing_time_ms = int(delta.total_seconds() * 1000)

    def set_result(self, response_text: str, confidence: int = None, sources_used: list = None):
        """Set successful result"""
        self.response_text = response_text
        self.confidence = confidence
        self.sources_used = sources_used
        self.update_progress(TaskStatus.COMPLETED, 100, "Response generated successfully")

    def set_error(self, error_message: str):
        """Set error result"""
        self.error_message = error_message
        self.update_progress(TaskStatus.FAILED, 0, f"Task failed: {error_message}")