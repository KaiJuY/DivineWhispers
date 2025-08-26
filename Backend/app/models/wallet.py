"""
Wallet model for user point balance management
"""

from datetime import datetime
from sqlalchemy import BigInteger, Integer, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .transaction import Transaction


class Wallet(Base):
    """Wallet model for managing user point balances"""
    __tablename__ = "wallets"
    
    # Primary Key
    wallet_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="錢包唯一 ID"
    )
    
    # Foreign Key to Users
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        comment="所屬使用者"
    )
    
    # Wallet balance
    balance: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="當前點數餘額"
    )
    
    # Timestamp for last update
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="最後更新時間"
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="wallets",
        lazy="select"
    )
    
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="wallet",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_wallets_user_id', 'user_id'),
        Index('idx_wallets_updated_at', 'updated_at'),
    )
    
    def has_sufficient_balance(self, amount: int) -> bool:
        """Check if wallet has sufficient balance for transaction"""
        return self.balance >= amount
    
    def deduct_balance(self, amount: int) -> bool:
        """Deduct amount from wallet balance"""
        if self.has_sufficient_balance(amount):
            self.balance -= amount
            return True
        return False
    
    def add_balance(self, amount: int) -> None:
        """Add amount to wallet balance"""
        self.balance += amount
    
    def get_balance(self) -> int:
        """Get current wallet balance"""
        return self.balance
    
    def __repr__(self) -> str:
        return f"<Wallet(wallet_id={self.wallet_id}, user_id={self.user_id}, balance={self.balance})>"