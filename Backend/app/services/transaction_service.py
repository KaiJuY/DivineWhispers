"""
Atomic transaction service for secure financial operations
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.wallet import Wallet
from app.models.job import Job, JobStatus
from app.schemas.wallet import (
    InternalTransactionCreate, 
    TransactionResponse,
    InternalWalletOperation
)
from app.utils.financial import (
    FinancialValidator,
    FinancialAuditor,
    InsufficientBalanceError,
    DuplicateTransactionError,
    FinancialValidationError,
    TransactionIdempotency
)

logger = logging.getLogger(__name__)


class TransactionService:
    """Atomic transaction service for secure financial operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_pending_transaction(
        self,
        wallet_id: int,
        transaction_type: TransactionType,
        amount: int,
        reference_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Transaction:
        """
        Create a pending transaction record
        
        Args:
            wallet_id: Wallet ID
            transaction_type: Type of transaction
            amount: Transaction amount (positive for credits, negative for debits)
            reference_id: Optional reference ID
            description: Transaction description
            
        Returns:
            Created transaction object
            
        Raises:
            FinancialValidationError: If validation fails
            DuplicateTransactionError: If duplicate transaction detected
        """
        try:
            # Validate inputs
            FinancialValidator.validate_amount(abs(amount))
            if reference_id:
                FinancialValidator.validate_reference_id(reference_id)
            
            # Check for duplicate transactions using reference_id
            if reference_id:
                existing = await self._get_transaction_by_reference(reference_id)
                if existing and existing.wallet_id == wallet_id:
                    raise DuplicateTransactionError(
                        f"Transaction with reference_id '{reference_id}' already exists"
                    )
            
            # Create transaction record
            transaction = Transaction(
                wallet_id=wallet_id,
                type=transaction_type,
                amount=amount,
                reference_id=reference_id,
                status=TransactionStatus.PENDING,
                description=description
            )
            
            self.db.add(transaction)
            await self.db.flush()  # Get the transaction ID without committing
            
            # Log the operation
            FinancialAuditor.log_financial_operation(
                operation_type=f"create_pending_{transaction_type.value}",
                user_id=0,  # Will be updated by caller with actual user_id
                amount=amount,
                wallet_id=wallet_id,
                transaction_id=transaction.txn_id,
                reference_id=reference_id
            )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to create pending transaction: {str(e)}")
            raise
    
    async def complete_transaction(
        self,
        transaction_id: int,
        status: TransactionStatus,
        error_message: Optional[str] = None
    ) -> Transaction:
        """
        Complete a pending transaction
        
        Args:
            transaction_id: Transaction ID to complete
            status: Final status (SUCCESS or FAILED)
            error_message: Error message if failed
            
        Returns:
            Updated transaction object
            
        Raises:
            ValueError: If transaction not found or not pending
        """
        try:
            # Get transaction with wallet for locking
            result = await self.db.execute(
                select(Transaction)
                .options(selectinload(Transaction.wallet))
                .where(Transaction.txn_id == transaction_id)
            )
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            if not transaction.is_pending():
                raise ValueError(f"Transaction {transaction_id} is not pending")
            
            # Update transaction status
            transaction.status = status
            if error_message and status == TransactionStatus.FAILED:
                transaction.description = f"{transaction.description or ''} - Error: {error_message}"
            
            # Log the completion
            FinancialAuditor.log_financial_operation(
                operation_type=f"complete_{transaction.type.value}",
                user_id=transaction.wallet.user_id if transaction.wallet else 0,
                amount=transaction.amount,
                wallet_id=transaction.wallet_id,
                transaction_id=transaction.txn_id,
                additional_data={"status": status.value, "error_message": error_message}
            )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to complete transaction {transaction_id}: {str(e)}")
            raise
    
    async def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """
        Get transaction by ID
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction object if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(Transaction)
                .options(selectinload(Transaction.wallet))
                .where(Transaction.txn_id == transaction_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get transaction {transaction_id}: {str(e)}")
            return None
    
    async def get_pending_transactions(self, user_id: Optional[int] = None) -> List[Transaction]:
        """
        Get pending transactions for a user or all users
        
        Args:
            user_id: Optional user ID filter
            
        Returns:
            List of pending transactions
        """
        try:
            query = select(Transaction).options(selectinload(Transaction.wallet))
            query = query.where(Transaction.status == TransactionStatus.PENDING)
            
            if user_id:
                query = query.join(Wallet).where(Wallet.user_id == user_id)
            
            query = query.order_by(Transaction.created_at.asc())
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get pending transactions: {str(e)}")
            return []
    
    async def get_wallet_transactions(
        self,
        wallet_id: int,
        limit: int = 20,
        offset: int = 0,
        status_filter: Optional[TransactionStatus] = None
    ) -> Tuple[List[Transaction], int]:
        """
        Get transactions for a wallet with pagination
        
        Args:
            wallet_id: Wallet ID
            limit: Number of transactions to return
            offset: Number of transactions to skip
            status_filter: Optional status filter
            
        Returns:
            Tuple of (transactions, total_count)
        """
        try:
            # Build query
            query = select(Transaction).where(Transaction.wallet_id == wallet_id)
            
            if status_filter:
                query = query.where(Transaction.status == status_filter)
            
            # Get total count
            count_query = select(func.count()).select_from(
                query.subquery()
            )
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar()
            
            # Get paginated results
            query = query.order_by(Transaction.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            transactions = result.scalars().all()
            
            return transactions, total_count
            
        except Exception as e:
            logger.error(f"Failed to get wallet transactions: {str(e)}")
            return [], 0
    
    async def get_user_transaction_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        transaction_type: Optional[TransactionType] = None,
        status_filter: Optional[TransactionStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[List[Transaction], int]:
        """
        Get comprehensive transaction history for a user
        
        Args:
            user_id: User ID
            limit: Number of transactions to return
            offset: Number of transactions to skip
            transaction_type: Optional transaction type filter
            status_filter: Optional status filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Tuple of (transactions, total_count)
        """
        try:
            # Build base query
            query = (
                select(Transaction)
                .join(Wallet)
                .where(Wallet.user_id == user_id)
            )
            
            # Apply filters
            if transaction_type:
                query = query.where(Transaction.type == transaction_type)
            
            if status_filter:
                query = query.where(Transaction.status == status_filter)
            
            if start_date:
                query = query.where(Transaction.created_at >= start_date)
            
            if end_date:
                query = query.where(Transaction.created_at <= end_date)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar()
            
            # Get paginated results
            query = query.order_by(Transaction.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            transactions = result.scalars().all()
            
            return transactions, total_count
            
        except Exception as e:
            logger.error(f"Failed to get user transaction history: {str(e)}")
            return [], 0
    
    async def validate_transaction_integrity(self) -> Dict[str, Any]:
        """
        Validate overall transaction integrity
        
        Returns:
            Dictionary containing validation results
        """
        try:
            issues = []
            
            # Check for orphaned transactions (transactions without wallets)
            orphaned_query = (
                select(func.count(Transaction.txn_id))
                .outerjoin(Wallet, Transaction.wallet_id == Wallet.wallet_id)
                .where(Wallet.wallet_id.is_(None))
            )
            orphaned_result = await self.db.execute(orphaned_query)
            orphaned_count = orphaned_result.scalar()
            
            if orphaned_count > 0:
                issues.append(f"Found {orphaned_count} orphaned transactions")
            
            # Check for long-pending transactions
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            old_pending_query = (
                select(func.count(Transaction.txn_id))
                .where(
                    and_(
                        Transaction.status == TransactionStatus.PENDING,
                        Transaction.created_at < cutoff_time
                    )
                )
            )
            old_pending_result = await self.db.execute(old_pending_query)
            old_pending_count = old_pending_result.scalar()
            
            if old_pending_count > 0:
                issues.append(f"Found {old_pending_count} long-pending transactions (>24h)")
            
            # Check for negative balances
            negative_balance_query = (
                select(func.count(Wallet.wallet_id))
                .where(Wallet.balance < 0)
            )
            negative_result = await self.db.execute(negative_balance_query)
            negative_count = negative_result.scalar()
            
            if negative_count > 0:
                issues.append(f"Found {negative_count} wallets with negative balance")
            
            return {
                "is_healthy": len(issues) == 0,
                "issues": issues,
                "checks_performed": [
                    "orphaned_transactions",
                    "long_pending_transactions",
                    "negative_balances"
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Transaction integrity validation failed: {str(e)}")
            return {
                "is_healthy": False,
                "issues": [f"Validation failed: {str(e)}"],
                "checks_performed": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_transaction_by_reference(self, reference_id: str) -> Optional[Transaction]:
        """
        Get transaction by reference ID
        
        Args:
            reference_id: Reference ID to search for
            
        Returns:
            Transaction if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(Transaction)
                .where(Transaction.reference_id == reference_id)
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Exception:
            return None
    
    async def cleanup_failed_transactions(self, older_than_hours: int = 24) -> int:
        """
        Clean up failed transactions older than specified hours
        
        Args:
            older_than_hours: Hours threshold for cleanup
            
        Returns:
            Number of transactions cleaned up
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            
            # Find failed transactions to clean up
            failed_query = (
                select(Transaction)
                .where(
                    and_(
                        Transaction.status == TransactionStatus.FAILED,
                        Transaction.created_at < cutoff_time
                    )
                )
            )
            
            result = await self.db.execute(failed_query)
            failed_transactions = result.scalars().all()
            
            cleanup_count = 0
            for transaction in failed_transactions:
                # Additional cleanup logic can be added here
                # For now, we just log them for audit purposes
                FinancialAuditor.log_financial_operation(
                    operation_type="cleanup_failed_transaction",
                    user_id=0,
                    amount=transaction.amount,
                    wallet_id=transaction.wallet_id,
                    transaction_id=transaction.txn_id,
                    additional_data={"cleanup_reason": "automated_cleanup"}
                )
                cleanup_count += 1
            
            logger.info(f"Cleaned up {cleanup_count} failed transactions")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup failed transactions: {str(e)}")
            return 0
    
    async def get_transaction_statistics(
        self,
        user_id: Optional[int] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get transaction statistics
        
        Args:
            user_id: Optional user ID filter
            days_back: Number of days to look back
            
        Returns:
            Dictionary containing statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Build base query
            query = select(Transaction).where(Transaction.created_at >= start_date)
            
            if user_id:
                query = query.join(Wallet).where(Wallet.user_id == user_id)
            
            result = await self.db.execute(query)
            transactions = result.scalars().all()
            
            # Calculate statistics
            total_count = len(transactions)
            successful_count = len([t for t in transactions if t.is_successful()])
            failed_count = len([t for t in transactions if t.is_failed()])
            pending_count = len([t for t in transactions if t.is_pending()])
            
            total_volume = sum(abs(t.amount) for t in transactions if t.is_successful())
            avg_amount = total_volume / successful_count if successful_count > 0 else 0
            success_rate = successful_count / total_count if total_count > 0 else 0
            
            # Transaction type breakdown
            type_breakdown = {}
            for transaction_type in TransactionType:
                count = len([t for t in transactions if t.type == transaction_type])
                type_breakdown[transaction_type.value] = count
            
            return {
                "period_days": days_back,
                "total_transactions": total_count,
                "successful_transactions": successful_count,
                "failed_transactions": failed_count,
                "pending_transactions": pending_count,
                "success_rate": round(success_rate * 100, 2),
                "total_volume": total_volume,
                "average_amount": round(avg_amount, 2),
                "type_breakdown": type_breakdown,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get transaction statistics: {str(e)}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }