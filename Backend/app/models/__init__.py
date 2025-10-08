"""SQLAlchemy database models"""

# Import base classes
from .base import Base, BaseModel, TimestampMixin

# Import all models
from .user import User, UserRole, UserStatus
from .wallet import Wallet
from .transaction import Transaction, TransactionType, TransactionStatus
from .job import Job, JobStatus
from .job_result import JobResult
from .audit_log import AuditLog
from .token_blacklist import TokenBlacklist, TokenType
from .chat_task import ChatTask, TaskStatus
from .email_verification import EmailVerificationToken

# Export all models and enums for easy importing
__all__ = [
    # Base classes
    "Base",
    "BaseModel", 
    "TimestampMixin",
    
    # Models
    "User",
    "Wallet",
    "Transaction",
    "Job",
    "JobResult",
    "AuditLog",
    "TokenBlacklist",
    "ChatTask",
    "EmailVerificationToken",

    # Enums
    "UserRole",
    "UserStatus",
    "TransactionType",
    "TransactionStatus",
    "JobStatus",
    "TokenType",
    "TaskStatus",
]