"""
Financial utilities and validation helpers for wallet transactions
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class FinancialValidationError(Exception):
    """Custom exception for financial validation errors"""
    pass

class InsufficientBalanceError(Exception):
    """Exception raised when wallet has insufficient balance"""
    pass

class DuplicateTransactionError(Exception):
    """Exception raised when attempting duplicate transaction"""
    pass

class FinancialValidator:
    """Financial validation and security utilities"""
    
    # Business rules constants
    MAX_SINGLE_TRANSACTION = 10000  # Maximum points per transaction
    MIN_TRANSACTION_AMOUNT = 1      # Minimum points per transaction
    MAX_DAILY_TRANSACTIONS = 100    # Maximum transactions per user per day
    MAX_DAILY_AMOUNT = 50000        # Maximum daily transaction amount per user
    
    @staticmethod
    def validate_amount(amount: int) -> None:
        """
        Validate transaction amount
        
        Args:
            amount: Transaction amount to validate
            
        Raises:
            FinancialValidationError: If amount is invalid
        """
        if not isinstance(amount, int):
            raise FinancialValidationError("Amount must be an integer")
            
        if amount <= 0:
            raise FinancialValidationError("Transaction amount must be positive")
            
        if amount > FinancialValidator.MAX_SINGLE_TRANSACTION:
            raise FinancialValidationError(
                f"Transaction amount exceeds maximum limit of {FinancialValidator.MAX_SINGLE_TRANSACTION}"
            )
            
        if amount < FinancialValidator.MIN_TRANSACTION_AMOUNT:
            raise FinancialValidationError(
                f"Transaction amount below minimum limit of {FinancialValidator.MIN_TRANSACTION_AMOUNT}"
            )
    
    @staticmethod
    def validate_balance(current_balance: int, amount: int) -> None:
        """
        Validate sufficient balance for transaction
        
        Args:
            current_balance: Current wallet balance
            amount: Amount to be deducted
            
        Raises:
            InsufficientBalanceError: If insufficient balance
        """
        if current_balance < amount:
            raise InsufficientBalanceError(
                f"Insufficient balance. Current: {current_balance}, Required: {amount}"
            )
    
    @staticmethod
    def validate_user_id(user_id: int) -> None:
        """
        Validate user ID
        
        Args:
            user_id: User ID to validate
            
        Raises:
            FinancialValidationError: If user_id is invalid
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise FinancialValidationError("User ID must be a positive integer")
    
    @staticmethod
    def validate_reference_id(reference_id: Optional[str]) -> None:
        """
        Validate reference ID format
        
        Args:
            reference_id: Reference ID to validate
            
        Raises:
            FinancialValidationError: If reference_id is invalid
        """
        if reference_id is not None:
            if not isinstance(reference_id, str):
                raise FinancialValidationError("Reference ID must be a string")
            if len(reference_id) > 255:
                raise FinancialValidationError("Reference ID too long (max 255 characters)")
            if len(reference_id.strip()) == 0:
                raise FinancialValidationError("Reference ID cannot be empty")


class TransactionIdempotency:
    """Handle transaction idempotency to prevent duplicate processing"""
    
    @staticmethod
    def generate_idempotency_key(user_id: int, amount: int, reference_id: Optional[str] = None) -> str:
        """
        Generate idempotency key for transaction
        
        Args:
            user_id: User ID
            amount: Transaction amount
            reference_id: Optional reference ID
            
        Returns:
            Unique idempotency key
        """
        # Create deterministic key based on transaction parameters
        key_data = f"user:{user_id}:amount:{amount}:ref:{reference_id or 'none'}"
        return f"txn_idem_{hash(key_data) % (10**10)}"
    
    @staticmethod
    def generate_unique_reference_id() -> str:
        """
        Generate unique reference ID for transactions
        
        Returns:
            Unique reference ID
        """
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        unique_id = str(uuid.uuid4()).replace('-', '')[:8]
        return f"dw_{timestamp}_{unique_id}"


class FinancialAuditor:
    """Financial audit and monitoring utilities"""
    
    @staticmethod
    def log_financial_operation(
        operation_type: str,
        user_id: int,
        amount: int,
        wallet_id: int,
        transaction_id: Optional[int] = None,
        reference_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log financial operation for audit purposes
        
        Args:
            operation_type: Type of operation (spend, deposit, refund, etc.)
            user_id: User ID
            amount: Transaction amount
            wallet_id: Wallet ID
            transaction_id: Transaction ID (if available)
            reference_id: Reference ID
            additional_data: Additional audit data
        """
        audit_data = {
            "operation_type": operation_type,
            "user_id": user_id,
            "wallet_id": wallet_id,
            "amount": amount,
            "transaction_id": transaction_id,
            "reference_id": reference_id,
            "timestamp": datetime.utcnow().isoformat(),
            "additional_data": additional_data or {}
        }
        
        logger.info(f"FINANCIAL_AUDIT: {audit_data}")
    
    @staticmethod
    def detect_suspicious_activity(
        user_id: int,
        recent_transactions: list,
        current_amount: int
    ) -> bool:
        """
        Detect potentially suspicious financial activity
        
        Args:
            user_id: User ID
            recent_transactions: List of recent transactions
            current_amount: Current transaction amount
            
        Returns:
            True if activity appears suspicious
        """
        # Check for rapid-fire transactions
        now = datetime.utcnow()
        recent_window = now - timedelta(minutes=5)
        
        recent_count = len([
            txn for txn in recent_transactions
            if txn.created_at > recent_window
        ])
        
        if recent_count > 10:  # More than 10 transactions in 5 minutes
            logger.warning(f"SUSPICIOUS_ACTIVITY: User {user_id} - {recent_count} transactions in 5 minutes")
            return True
        
        # Check for unusually large amounts
        if current_amount > FinancialValidator.MAX_SINGLE_TRANSACTION * 0.8:
            logger.warning(f"SUSPICIOUS_ACTIVITY: User {user_id} - Large transaction: {current_amount}")
            return True
        
        return False


class ConcurrencyManager:
    """Handle concurrency and race condition prevention"""
    
    @staticmethod
    def generate_lock_key(resource_type: str, resource_id: int) -> str:
        """
        Generate lock key for resource
        
        Args:
            resource_type: Type of resource (wallet, user, etc.)
            resource_id: Resource ID
            
        Returns:
            Lock key string
        """
        return f"lock:{resource_type}:{resource_id}"
    
    @staticmethod
    def is_amount_safe_for_concurrent_ops(amount: int) -> bool:
        """
        Check if amount is safe for concurrent operations
        
        Args:
            amount: Transaction amount
            
        Returns:
            True if amount is safe for concurrent processing
        """
        # Large amounts should be processed with extra care
        return amount <= 1000


class FinancialReporting:
    """Financial reporting and analytics utilities"""
    
    @staticmethod
    def calculate_transaction_metrics(transactions: list) -> Dict[str, Any]:
        """
        Calculate transaction metrics
        
        Args:
            transactions: List of transactions
            
        Returns:
            Dictionary containing metrics
        """
        if not transactions:
            return {
                "total_count": 0,
                "total_amount": 0,
                "average_amount": 0,
                "min_amount": 0,
                "max_amount": 0
            }
        
        amounts = [abs(txn.amount) for txn in transactions]
        
        return {
            "total_count": len(transactions),
            "total_amount": sum(amounts),
            "average_amount": sum(amounts) / len(amounts),
            "min_amount": min(amounts),
            "max_amount": max(amounts),
            "success_rate": len([txn for txn in transactions if txn.is_successful()]) / len(transactions)
        }
    
    @staticmethod
    def generate_balance_summary(wallet_balance: int, pending_amount: int = 0) -> Dict[str, Any]:
        """
        Generate wallet balance summary
        
        Args:
            wallet_balance: Current wallet balance
            pending_amount: Amount in pending transactions
            
        Returns:
            Balance summary dictionary
        """
        return {
            "current_balance": wallet_balance,
            "pending_amount": pending_amount,
            "available_balance": wallet_balance - pending_amount,
            "last_updated": datetime.utcnow().isoformat()
        }


# Utility functions for common operations
def format_amount(amount: int) -> str:
    """Format amount for display"""
    return f"{amount:,} points"

def format_transaction_description(
    transaction_type: str,
    amount: int,
    reference_id: Optional[str] = None
) -> str:
    """
    Format transaction description
    
    Args:
        transaction_type: Type of transaction
        amount: Transaction amount
        reference_id: Optional reference ID
        
    Returns:
        Formatted description string
    """
    base_desc = f"{transaction_type.title()}: {format_amount(amount)}"
    if reference_id:
        base_desc += f" (Ref: {reference_id})"
    return base_desc

def is_valid_points_amount(amount: Any) -> bool:
    """
    Check if value is a valid points amount
    
    Args:
        amount: Value to check
        
    Returns:
        True if valid points amount
    """
    try:
        if isinstance(amount, str):
            amount = int(amount)
        return isinstance(amount, int) and amount > 0
    except (ValueError, TypeError):
        return False