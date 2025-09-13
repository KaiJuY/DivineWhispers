"""
AuditLog model for tracking user actions and system events
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import BigInteger, Integer, String, Text, ForeignKey, DateTime, func, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, TYPE_CHECKING

from .base import Base


class ActionType(str, Enum):
    """Enumeration of audit log action types"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ACCESS = "ACCESS"
    ACCESS_DENIED = "ACCESS_DENIED"
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"
    FORTUNE_DRAW = "FORTUNE_DRAW"
    FORTUNE_INTERPRET = "FORTUNE_INTERPRET"
    JOB_CREATE = "JOB_CREATE"
    JOB_COMPLETE = "JOB_COMPLETE"
    JOB_FAILED = "JOB_FAILED"
    SYSTEM_ACTION = "SYSTEM_ACTION"
    USER_REGISTER = "USER_REGISTER"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    ROLE_CHANGE = "ROLE_CHANGE"
    STATUS_CHANGE = "STATUS_CHANGE"
    BALANCE_ADJUSTMENT = "BALANCE_ADJUSTMENT"

if TYPE_CHECKING:
    from .user import User


class AuditLog(Base):
    """AuditLog model for tracking user actions and system events"""
    __tablename__ = "audit_logs"
    
    # Primary Key
    log_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Log 唯一 ID"
    )
    
    # Foreign Key to Users (nullable for system actions)
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        comment="誰觸發的操作"
    )
    
    # Action details
    action: Mapped[ActionType] = mapped_column(
        String(50),
        nullable=False,
        comment="動作類型"
    )
    
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="操作詳細信息"
    )
    
    # Additional context
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="操作的資源類型（user / job / transaction / ...）"
    )
    
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="操作的資源 ID"
    )
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="用戶 IP 地址"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="用戶瀏覽器信息"
    )
    
    session_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="會話 ID"
    )
    
    # Status and result
    status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="操作狀態（success / failed / error）"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="錯誤訊息（如果操作失敗）"
    )
    
    # Structured details (JSON)
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="結構化的額外信息"
    )
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="發生時間"
    )
    
    @property
    def created_at(self) -> datetime:
        """Alias for timestamp for backwards compatibility"""
        return self.timestamp
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
        lazy="select"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_logs_user_id', 'user_id'),
        Index('idx_audit_logs_action', 'action'),
        Index('idx_audit_logs_created_at', 'created_at'),
        Index('idx_audit_logs_status', 'status'),
        Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_logs_ip_address', 'ip_address'),
        Index('idx_audit_logs_user_action', 'user_id', 'action'),
        Index('idx_audit_logs_action_created', 'action', 'created_at'),
    )
    
    @classmethod
    def create_login_log(
        cls,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success"
    ) -> "AuditLog":
        """Create a login audit log entry"""
        return cls(
            user_id=user_id,
            action=ActionType.LOGIN,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type="user",
            resource_id=str(user_id)
        )
    
    @classmethod
    def create_logout_log(
        cls,
        user_id: int,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> "AuditLog":
        """Create a logout audit log entry"""
        return cls(
            user_id=user_id,
            action=ActionType.LOGOUT,
            status="success",
            ip_address=ip_address,
            session_id=session_id,
            resource_type="user",
            resource_id=str(user_id)
        )
    
    @classmethod
    def create_transaction_log(
        cls,
        user_id: int,
        action: ActionType,
        transaction_id: int,
        amount: int,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None
    ) -> "AuditLog":
        """Create a transaction audit log entry"""
        return cls(
            user_id=user_id,
            action=action,
            status=status,
            details=details,
            resource_type="transaction",
            resource_id=str(transaction_id),
            extra_data={"amount": amount}
        )
    
    @classmethod
    def create_job_log(
        cls,
        user_id: int,
        action: ActionType,
        job_id: int,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> "AuditLog":
        """Create a job audit log entry"""
        return cls(
            user_id=user_id,
            action=action,
            status=status,
            details=details,
            resource_type="job",
            resource_id=str(job_id),
            extra_data=extra_data
        )
    
    @classmethod
    def create_system_log(
        cls,
        action: ActionType,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        extra_data: Optional[Dict[str, Any]] = None
    ) -> "AuditLog":
        """Create a system audit log entry"""
        return cls(
            user_id=None,
            action=action,
            status=status,
            details=details,
            resource_type="system",
            extra_data=extra_data
        )
    
    def is_successful(self) -> bool:
        """Check if the logged action was successful"""
        return self.status == "success"
    
    def is_failed(self) -> bool:
        """Check if the logged action failed"""
        return self.status in ["failed", "error"]
    
    def get_user_display(self) -> str:
        """Get user display string"""
        if self.user_id:
            return f"User {self.user_id}"
        return "System"
    
    def __repr__(self) -> str:
        return (
            f"<AuditLog(log_id={self.log_id}, user_id={self.user_id}, "
            f"action='{self.action.value}', status='{self.status}', timestamp={self.timestamp})>"
        )