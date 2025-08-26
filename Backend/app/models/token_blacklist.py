"""
Token blacklist model for JWT revocation and logout functionality
"""

import enum
from sqlalchemy import String, DateTime, Enum, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from .base import BaseModel


class TokenType(enum.Enum):
    """Token type enumeration"""
    ACCESS = "access"
    REFRESH = "refresh"


class TokenBlacklist(BaseModel):
    """Token blacklist model for revoking JWT tokens"""
    __tablename__ = "token_blacklist"
    
    # JWT ID (unique identifier from the token)
    jti: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        comment="JWT ID from token payload"
    )
    
    # Token type
    token_type: Mapped[TokenType] = mapped_column(
        Enum(TokenType),
        nullable=False,
        comment="Type of token (access/refresh)"
    )
    
    # User ID who owned the token
    user_id: Mapped[int] = mapped_column(
        nullable=False,
        comment="User ID who owned this token"
    )
    
    # Token expiration time (for cleanup)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Original expiration time of the token"
    )
    
    # Reason for blacklisting
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default="logout",
        comment="Reason for blacklisting (logout, security_breach, etc.)"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_token_blacklist_jti', 'jti'),
        Index('idx_token_blacklist_user_id', 'user_id'),
        Index('idx_token_blacklist_expires_at', 'expires_at'),
        Index('idx_token_blacklist_token_type', 'token_type'),
        Index('idx_token_blacklist_created_at', 'created_at'),
    )
    
    def is_expired(self) -> bool:
        """Check if the blacklisted token has already expired"""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self) -> str:
        return f"<TokenBlacklist(jti='{self.jti}', user_id={self.user_id}, token_type={self.token_type.value}, reason='{self.reason}')>"