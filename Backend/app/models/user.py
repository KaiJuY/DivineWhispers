"""
User model for authentication and user management
"""

import enum
from sqlalchemy import BigInteger, String, Integer, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING

from .base import BaseModel

if TYPE_CHECKING:
    from .wallet import Wallet
    from .job import Job
    from .audit_log import AuditLog
    from .chat_message import ChatSession


class UserRole(enum.Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class UserStatus(enum.Enum):
    """User status enumeration"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    BANNED = "banned"


class User(BaseModel):
    """User model for system users"""
    __tablename__ = "users"
    
    # Primary Key
    user_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="使用者唯一 ID"
    )
    
    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="登入帳號"
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="加鹽後 hash 密碼"
    )
    
    # User metadata
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.USER,
        nullable=False,
        comment="使用者角色"
    )
    
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus),
        default=UserStatus.ACTIVE,
        nullable=False,
        comment="使用者狀態"
    )
    
    points_balance: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="目前剩餘點數"
    )
    
    # Profile fields
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="使用者全名"
    )
    
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="電話號碼"
    )
    
    birth_date: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="生日 (YYYY-MM-DD)"
    )
    
    location: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="居住地點"
    )
    
    preferred_language: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        default="en",
        comment="偏好語言"
    )
    
    # Relationships
    wallets: Mapped[List["Wallet"]] = relationship(
        "Wallet",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    jobs: Mapped[List["Job"]] = relationship(
        "Job",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )

    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_status', 'status'),
        Index('idx_users_role', 'role'),
        Index('idx_users_created_at', 'created_at'),
    )
    
    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    def has_sufficient_points(self, required_points: int) -> bool:
        """Check if user has sufficient points for operation"""
        return self.points_balance >= required_points
    
    def deduct_points(self, amount: int) -> bool:
        """Deduct points from user balance"""
        if self.has_sufficient_points(amount):
            self.points_balance -= amount
            return True
        return False
    
    def add_points(self, amount: int) -> None:
        """Add points to user balance"""
        self.points_balance += amount
    
    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, email='{self.email}', role={self.role.value}, status={self.status.value})>"