"""
Transaction model for tracking point transactions
"""

import enum
from sqlalchemy import BigInteger, String, Integer, ForeignKey, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from .base import BaseModel

if TYPE_CHECKING:
    from .wallet import Wallet
    from .job import Job


class TransactionType(enum.Enum):
    """Transaction type enumeration"""
    DEPOSIT = "deposit"
    SPEND = "spend"
    REFUND = "refund"


class TransactionStatus(enum.Enum):
    """Transaction status enumeration"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Transaction(BaseModel):
    """Transaction model for tracking point movements"""
    __tablename__ = "transactions"
    
    # Primary Key
    txn_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="交易唯一 ID"
    )
    
    # Foreign Key to Wallets
    wallet_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("wallets.wallet_id", ondelete="CASCADE"),
        nullable=False,
        comment="所屬錢包"
    )
    
    # Transaction details
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType),
        nullable=False,
        comment="交易類型"
    )
    
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="金額（正數 = 加點，負數 = 扣點）"
    )
    
    reference_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="金流平台或任務 ID"
    )
    
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus),
        default=TransactionStatus.PENDING,
        nullable=False,
        comment="狀態"
    )
    
    # Additional metadata
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="交易描述"
    )

    payment_method: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="付款方式 (credit_card, paypal, apple_pay, google_pay, etc.)"
    )
    
    # Relationships
    wallet: Mapped["Wallet"] = relationship(
        "Wallet",
        back_populates="transactions",
        lazy="select"
    )
    
    job: Mapped[Optional["Job"]] = relationship(
        "Job",
        back_populates="transaction",
        lazy="select"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_transactions_wallet_id', 'wallet_id'),
        Index('idx_transactions_type', 'type'),
        Index('idx_transactions_status', 'status'),
        Index('idx_transactions_reference_id', 'reference_id'),
        Index('idx_transactions_created_at', 'created_at'),
        Index('idx_transactions_wallet_status', 'wallet_id', 'status'),
    )
    
    def is_successful(self) -> bool:
        """Check if transaction is successful"""
        return self.status == TransactionStatus.SUCCESS
    
    def is_pending(self) -> bool:
        """Check if transaction is pending"""
        return self.status == TransactionStatus.PENDING
    
    def is_failed(self) -> bool:
        """Check if transaction is failed"""
        return self.status == TransactionStatus.FAILED
    
    def mark_success(self) -> None:
        """Mark transaction as successful"""
        self.status = TransactionStatus.SUCCESS
    
    def mark_failed(self) -> None:
        """Mark transaction as failed"""
        self.status = TransactionStatus.FAILED
    
    def get_absolute_amount(self) -> int:
        """Get absolute amount regardless of sign"""
        return abs(self.amount)
    
    def is_credit(self) -> bool:
        """Check if transaction adds points (positive amount)"""
        return self.amount > 0
    
    def is_debit(self) -> bool:
        """Check if transaction deducts points (negative amount)"""
        return self.amount < 0
    
    def __repr__(self) -> str:
        return (
            f"<Transaction(txn_id={self.txn_id}, wallet_id={self.wallet_id}, "
            f"type={self.type.value}, amount={self.amount}, status={self.status.value})>"
        )