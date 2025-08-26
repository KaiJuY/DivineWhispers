"""
Pydantic schemas for wallet and transaction operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.models.transaction import TransactionType, TransactionStatus
from app.utils.financial import FinancialValidator, is_valid_points_amount


class TransactionTypeSchema(str, Enum):
    """Transaction type schema"""
    DEPOSIT = "deposit"
    SPEND = "spend"
    REFUND = "refund"
    TRANSFER = "transfer"


class TransactionStatusSchema(str, Enum):
    """Transaction status schema"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


# Request schemas
class SpendPointsRequest(BaseModel):
    """Request schema for spending points"""
    amount: int = Field(..., gt=0, le=10000, description="Points to spend")
    job_type: str = Field(..., min_length=1, max_length=100, description="Type of job/service")
    description: Optional[str] = Field(None, max_length=500, description="Transaction description")
    
    @validator('amount')
    def validate_amount(cls, v):
        if not is_valid_points_amount(v):
            raise ValueError("Invalid points amount")
        FinancialValidator.validate_amount(v)
        return v


class DepositPointsRequest(BaseModel):
    """Request schema for depositing points"""
    amount: int = Field(..., gt=0, le=10000, description="Points to deposit")
    reference_id: Optional[str] = Field(None, max_length=255, description="Payment reference ID")
    description: Optional[str] = Field(None, max_length=500, description="Transaction description")
    
    @validator('amount')
    def validate_amount(cls, v):
        if not is_valid_points_amount(v):
            raise ValueError("Invalid points amount")
        FinancialValidator.validate_amount(v)
        return v
    
    @validator('reference_id')
    def validate_reference_id(cls, v):
        if v is not None:
            FinancialValidator.validate_reference_id(v)
        return v


class RefundRequest(BaseModel):
    """Request schema for refunding points"""
    original_transaction_id: int = Field(..., gt=0, description="Original transaction ID to refund")
    amount: Optional[int] = Field(None, gt=0, le=10000, description="Partial refund amount (optional)")
    reason: str = Field(..., min_length=1, max_length=500, description="Refund reason")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v is not None:
            if not is_valid_points_amount(v):
                raise ValueError("Invalid points amount")
            FinancialValidator.validate_amount(v)
        return v


class TransferPointsRequest(BaseModel):
    """Request schema for transferring points between users"""
    to_user_id: int = Field(..., gt=0, description="Recipient user ID")
    amount: int = Field(..., gt=0, le=1000, description="Points to transfer (max 1000)")
    description: str = Field(..., min_length=1, max_length=500, description="Transfer description")
    
    @validator('amount')
    def validate_amount(cls, v):
        if not is_valid_points_amount(v):
            raise ValueError("Invalid points amount")
        # Lower limit for transfers
        if v > 1000:
            raise ValueError("Transfer amount cannot exceed 1000 points")
        FinancialValidator.validate_amount(v)
        return v


class AdminPointAdjustmentRequest(BaseModel):
    """Request schema for admin point adjustments"""
    user_id: int = Field(..., gt=0, description="Target user ID")
    amount: int = Field(..., description="Points to add (positive) or deduct (negative)")
    reason: str = Field(..., min_length=1, max_length=500, description="Adjustment reason")
    
    @validator('amount')
    def validate_amount(cls, v):
        if not isinstance(v, int):
            raise ValueError("Amount must be an integer")
        if v == 0:
            raise ValueError("Amount cannot be zero")
        # Admin can adjust larger amounts
        if abs(v) > 50000:
            raise ValueError("Admin adjustment cannot exceed 50,000 points")
        return v


class TransactionHistoryQuery(BaseModel):
    """Query parameters for transaction history"""
    limit: int = Field(20, ge=1, le=100, description="Number of transactions to return")
    offset: int = Field(0, ge=0, description="Number of transactions to skip")
    transaction_type: Optional[TransactionTypeSchema] = Field(None, description="Filter by transaction type")
    status: Optional[TransactionStatusSchema] = Field(None, description="Filter by transaction status")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")


# Response schemas
class TransactionResponse(BaseModel):
    """Response schema for transaction details"""
    txn_id: int
    wallet_id: int
    type: TransactionTypeSchema
    amount: int
    status: TransactionStatusSchema
    reference_id: Optional[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WalletBalanceResponse(BaseModel):
    """Response schema for wallet balance"""
    wallet_id: int
    user_id: int
    balance: int
    pending_amount: int
    available_balance: int
    last_updated: datetime
    
    @validator('available_balance', always=True)
    def calculate_available_balance(cls, v, values):
        balance = values.get('balance', 0)
        pending = values.get('pending_amount', 0)
        return balance - pending


class WalletResponse(BaseModel):
    """Complete wallet response with balance and recent transactions"""
    wallet_id: int
    user_id: int
    balance: int
    pending_amount: int
    available_balance: int
    last_updated: datetime
    recent_transactions: List[TransactionResponse]
    
    class Config:
        from_attributes = True


class TransactionHistoryResponse(BaseModel):
    """Response schema for transaction history"""
    transactions: List[TransactionResponse]
    total_count: int
    page_info: dict
    summary: dict


class SpendPointsResponse(BaseModel):
    """Response schema for spending points"""
    transaction: TransactionResponse
    job_id: Optional[int]
    remaining_balance: int
    message: str


class DepositPointsResponse(BaseModel):
    """Response schema for depositing points"""
    transaction: TransactionResponse
    new_balance: int
    message: str


class RefundResponse(BaseModel):
    """Response schema for refund operations"""
    refund_transaction: TransactionResponse
    original_transaction: TransactionResponse
    new_balance: int
    message: str


class TransferResponse(BaseModel):
    """Response schema for point transfers"""
    sender_transaction: TransactionResponse
    receiver_transaction: TransactionResponse
    sender_balance: int
    receiver_balance: int
    message: str


class AdminWalletSummary(BaseModel):
    """Admin view of wallet summary"""
    wallet_id: int
    user_id: int
    username: Optional[str]
    email: Optional[str]
    balance: int
    pending_amount: int
    total_deposits: int
    total_spending: int
    transaction_count: int
    last_transaction_date: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdminTransactionSummary(BaseModel):
    """Admin view of transaction summary"""
    total_transactions: int
    total_volume: int
    successful_transactions: int
    failed_transactions: int
    pending_transactions: int
    success_rate: float
    avg_transaction_amount: float
    date_range: dict


# Error response schemas
class WalletErrorResponse(BaseModel):
    """Error response schema for wallet operations"""
    error_code: str
    error_message: str
    details: Optional[dict] = None


class InsufficientBalanceResponse(WalletErrorResponse):
    """Insufficient balance error response"""
    error_code: str = "INSUFFICIENT_BALANCE"
    current_balance: int
    required_amount: int
    shortfall: int


class DuplicateTransactionResponse(WalletErrorResponse):
    """Duplicate transaction error response"""
    error_code: str = "DUPLICATE_TRANSACTION"
    existing_transaction_id: int


# Validation schemas
class BalanceValidationResponse(BaseModel):
    """Balance validation response"""
    is_sufficient: bool
    current_balance: int
    required_amount: int
    shortfall: Optional[int] = None


class TransactionValidationResponse(BaseModel):
    """Transaction validation response"""
    is_valid: bool
    validation_errors: List[str] = []
    warnings: List[str] = []


# Internal operation schemas
class InternalTransactionCreate(BaseModel):
    """Internal schema for creating transactions"""
    wallet_id: int
    type: TransactionTypeSchema
    amount: int
    reference_id: Optional[str] = None
    description: Optional[str] = None
    status: TransactionStatusSchema = TransactionStatusSchema.PENDING


class InternalWalletOperation(BaseModel):
    """Internal schema for wallet operations"""
    operation_type: str  # spend, deposit, refund, transfer
    user_id: int
    amount: int
    reference_id: Optional[str] = None
    description: Optional[str] = None
    job_id: Optional[int] = None
    target_user_id: Optional[int] = None  # For transfers
    idempotency_key: Optional[str] = None