"""
High-level wallet service with atomic transaction processing
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.models.wallet import Wallet
from app.models.user import User
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.job import Job, JobStatus
from app.services.transaction_service import TransactionService
from app.schemas.wallet import (
    WalletBalanceResponse,
    TransactionResponse,
    TransactionHistoryResponse,
    SpendPointsResponse,
    DepositPointsResponse,
    RefundResponse,
    TransferResponse
)
from app.utils.financial import (
    FinancialValidator,
    FinancialAuditor,
    InsufficientBalanceError,
    DuplicateTransactionError,
    FinancialValidationError,
    TransactionIdempotency,
    FinancialReporting
)

logger = logging.getLogger(__name__)


class WalletService:
    """High-level wallet service with atomic transaction processing"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.transaction_service = TransactionService(db_session)
    
    async def spend_points(
        self,
        user_id: int,
        amount: int,
        job_type: str,
        description: Optional[str] = None
    ) -> Tuple[Transaction, Job]:
        """
        Atomically spend points and create job
        
        Args:
            user_id: User ID
            amount: Points to spend
            job_type: Type of job being created
            description: Transaction description
            
        Returns:
            Tuple of (transaction, job)
            
        Raises:
            InsufficientBalanceError: If insufficient balance
            FinancialValidationError: If validation fails
        """
        async with self.db.begin():  # Start atomic transaction
            try:
                # Validate inputs
                FinancialValidator.validate_user_id(user_id)
                FinancialValidator.validate_amount(amount)
                
                # Get wallet with row locking to prevent race conditions
                wallet = await self._get_wallet_with_lock(user_id)
                if not wallet:
                    raise FinancialValidationError(f"Wallet not found for user {user_id}")
                
                # Validate sufficient balance
                FinancialValidator.validate_balance(wallet.balance, amount)
                
                # Check for suspicious activity
                recent_transactions = await self._get_recent_transactions(user_id, hours=1)
                if FinancialAuditor.detect_suspicious_activity(user_id, recent_transactions, amount):
                    logger.warning(f"Suspicious spending activity detected for user {user_id}")
                
                # Generate reference ID for this spend operation
                reference_id = TransactionIdempotency.generate_unique_reference_id()
                
                # Create pending transaction
                transaction = await self.transaction_service.create_pending_transaction(
                    wallet_id=wallet.wallet_id,
                    transaction_type=TransactionType.SPEND,
                    amount=-amount,  # Negative for spending
                    reference_id=reference_id,
                    description=description or f"Points spent for {job_type}"
                )
                
                # Deduct points from wallet
                if not wallet.deduct_balance(amount):
                    raise InsufficientBalanceError(f"Failed to deduct {amount} points from wallet")
                
                # Create job record
                job = Job(
                    user_id=user_id,
                    txn_id=transaction.txn_id,
                    status=JobStatus.PENDING,
                    points_used=amount,
                    job_type=job_type,
                    priority=0
                )
                
                self.db.add(job)
                await self.db.flush()  # Get job ID
                
                # Complete transaction as successful
                await self.transaction_service.complete_transaction(
                    transaction.txn_id,
                    TransactionStatus.SUCCESS
                )
                
                # Audit logging
                FinancialAuditor.log_financial_operation(
                    operation_type="spend_points",
                    user_id=user_id,
                    amount=amount,
                    wallet_id=wallet.wallet_id,
                    transaction_id=transaction.txn_id,
                    reference_id=reference_id,
                    additional_data={"job_id": job.job_id, "job_type": job_type}
                )
                
                logger.info(f"Successfully spent {amount} points for user {user_id}, job {job.job_id}")
                return transaction, job
                
            except Exception as e:
                # Transaction will be automatically rolled back
                logger.error(f"Failed to spend points for user {user_id}: {str(e)}")
                
                # Mark transaction as failed if it was created
                if 'transaction' in locals():
                    try:
                        await self.transaction_service.complete_transaction(
                            transaction.txn_id,
                            TransactionStatus.FAILED,
                            str(e)
                        )
                    except Exception:
                        pass  # Transaction rollback will handle this
                
                raise
    
    async def deposit_points(
        self,
        user_id: int,
        amount: int,
        reference_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Transaction:
        """
        Atomically deposit points to user wallet
        
        Args:
            user_id: User ID
            amount: Points to deposit
            reference_id: Payment reference ID
            description: Transaction description
            
        Returns:
            Transaction object
            
        Raises:
            FinancialValidationError: If validation fails
            DuplicateTransactionError: If duplicate reference_id
        """
        async with self.db.begin():
            try:
                # Validate inputs
                FinancialValidator.validate_user_id(user_id)
                FinancialValidator.validate_amount(amount)
                if reference_id:
                    FinancialValidator.validate_reference_id(reference_id)
                
                # Get or create wallet
                wallet = await self._get_or_create_wallet(user_id)
                
                # Generate reference if not provided
                if not reference_id:
                    reference_id = TransactionIdempotency.generate_unique_reference_id()
                
                # Create pending transaction
                transaction = await self.transaction_service.create_pending_transaction(
                    wallet_id=wallet.wallet_id,
                    transaction_type=TransactionType.DEPOSIT,
                    amount=amount,  # Positive for deposit
                    reference_id=reference_id,
                    description=description or f"Deposit of {amount} points"
                )
                
                # Add points to wallet
                wallet.add_balance(amount)
                
                # Complete transaction as successful
                await self.transaction_service.complete_transaction(
                    transaction.txn_id,
                    TransactionStatus.SUCCESS
                )
                
                # Audit logging
                FinancialAuditor.log_financial_operation(
                    operation_type="deposit_points",
                    user_id=user_id,
                    amount=amount,
                    wallet_id=wallet.wallet_id,
                    transaction_id=transaction.txn_id,
                    reference_id=reference_id
                )
                
                logger.info(f"Successfully deposited {amount} points for user {user_id}")
                return transaction
                
            except Exception as e:
                logger.error(f"Failed to deposit points for user {user_id}: {str(e)}")
                
                # Mark transaction as failed if it was created
                if 'transaction' in locals():
                    try:
                        await self.transaction_service.complete_transaction(
                            transaction.txn_id,
                            TransactionStatus.FAILED,
                            str(e)
                        )
                    except Exception:
                        pass
                
                raise
    
    async def refund_points(
        self,
        original_transaction_id: int,
        amount: Optional[int] = None,
        reason: str = "Refund processed"
    ) -> Tuple[Transaction, Transaction]:
        """
        Process refund for a transaction
        
        Args:
            original_transaction_id: Original transaction ID to refund
            amount: Partial refund amount (None for full refund)
            reason: Refund reason
            
        Returns:
            Tuple of (refund_transaction, original_transaction)
            
        Raises:
            FinancialValidationError: If validation fails
        """
        async with self.db.begin():
            try:
                # Get original transaction
                original_txn = await self.transaction_service.get_transaction_by_id(
                    original_transaction_id
                )
                
                if not original_txn:
                    raise FinancialValidationError(
                        f"Original transaction {original_transaction_id} not found"
                    )
                
                if not original_txn.is_successful():
                    raise FinancialValidationError(
                        "Can only refund successful transactions"
                    )
                
                if original_txn.type != TransactionType.SPEND:
                    raise FinancialValidationError(
                        "Can only refund spending transactions"
                    )
                
                # Calculate refund amount
                refund_amount = amount or abs(original_txn.amount)
                max_refund = abs(original_txn.amount)
                
                if refund_amount > max_refund:
                    raise FinancialValidationError(
                        f"Refund amount {refund_amount} exceeds original amount {max_refund}"
                    )
                
                # Get wallet with locking
                wallet = await self._get_wallet_by_id_with_lock(original_txn.wallet_id)
                if not wallet:
                    raise FinancialValidationError("Wallet not found")
                
                # Generate reference ID for refund
                reference_id = f"refund_{original_transaction_id}_{int(datetime.utcnow().timestamp())}"
                
                # Create refund transaction
                refund_txn = await self.transaction_service.create_pending_transaction(
                    wallet_id=wallet.wallet_id,
                    transaction_type=TransactionType.REFUND,
                    amount=refund_amount,  # Positive for refund
                    reference_id=reference_id,
                    description=f"Refund for transaction {original_transaction_id}: {reason}"
                )
                
                # Add refund points to wallet
                wallet.add_balance(refund_amount)
                
                # Complete refund transaction
                await self.transaction_service.complete_transaction(
                    refund_txn.txn_id,
                    TransactionStatus.SUCCESS
                )
                
                # Update original job status if exists
                if original_txn.job:
                    original_txn.job.mark_failed(f"Refunded: {reason}")
                
                # Audit logging
                FinancialAuditor.log_financial_operation(
                    operation_type="refund_points",
                    user_id=wallet.user_id,
                    amount=refund_amount,
                    wallet_id=wallet.wallet_id,
                    transaction_id=refund_txn.txn_id,
                    reference_id=reference_id,
                    additional_data={
                        "original_transaction_id": original_transaction_id,
                        "refund_reason": reason
                    }
                )
                
                logger.info(f"Successfully refunded {refund_amount} points for transaction {original_transaction_id}")
                return refund_txn, original_txn
                
            except Exception as e:
                logger.error(f"Failed to refund transaction {original_transaction_id}: {str(e)}")
                raise
    
    async def transfer_points(
        self,
        from_user_id: int,
        to_user_id: int,
        amount: int,
        description: str
    ) -> Tuple[Transaction, Transaction]:
        """
        Transfer points between users
        
        Args:
            from_user_id: Source user ID
            to_user_id: Destination user ID
            amount: Points to transfer
            description: Transfer description
            
        Returns:
            Tuple of (sender_transaction, receiver_transaction)
            
        Raises:
            FinancialValidationError: If validation fails
            InsufficientBalanceError: If insufficient balance
        """
        async with self.db.begin():
            try:
                # Validate inputs
                FinancialValidator.validate_user_id(from_user_id)
                FinancialValidator.validate_user_id(to_user_id)
                FinancialValidator.validate_amount(amount)
                
                if from_user_id == to_user_id:
                    raise FinancialValidationError("Cannot transfer points to yourself")
                
                # Limit transfer amounts
                if amount > 1000:
                    raise FinancialValidationError("Transfer amount cannot exceed 1000 points")
                
                # Get both wallets with locking (order by ID to prevent deadlocks)
                if from_user_id < to_user_id:
                    from_wallet = await self._get_wallet_with_lock(from_user_id)
                    to_wallet = await self._get_or_create_wallet(to_user_id)
                else:
                    to_wallet = await self._get_or_create_wallet(to_user_id)
                    from_wallet = await self._get_wallet_with_lock(from_user_id)
                
                if not from_wallet:
                    raise FinancialValidationError(f"Source wallet not found for user {from_user_id}")
                
                # Validate sufficient balance
                FinancialValidator.validate_balance(from_wallet.balance, amount)
                
                # Generate reference ID for transfer pair
                reference_base = TransactionIdempotency.generate_unique_reference_id()
                
                # Create sender transaction (debit)
                sender_txn = await self.transaction_service.create_pending_transaction(
                    wallet_id=from_wallet.wallet_id,
                    transaction_type=TransactionType.SPEND,  # Using SPEND for debit side
                    amount=-amount,
                    reference_id=f"{reference_base}_send",
                    description=f"Transfer to user {to_user_id}: {description}"
                )
                
                # Create receiver transaction (credit)
                receiver_txn = await self.transaction_service.create_pending_transaction(
                    wallet_id=to_wallet.wallet_id,
                    transaction_type=TransactionType.DEPOSIT,
                    amount=amount,
                    reference_id=f"{reference_base}_receive",
                    description=f"Transfer from user {from_user_id}: {description}"
                )
                
                # Execute the transfer
                if not from_wallet.deduct_balance(amount):
                    raise InsufficientBalanceError("Failed to deduct transfer amount")
                
                to_wallet.add_balance(amount)
                
                # Complete both transactions
                await self.transaction_service.complete_transaction(
                    sender_txn.txn_id,
                    TransactionStatus.SUCCESS
                )
                
                await self.transaction_service.complete_transaction(
                    receiver_txn.txn_id,
                    TransactionStatus.SUCCESS
                )
                
                # Audit logging for both sides
                FinancialAuditor.log_financial_operation(
                    operation_type="transfer_points_send",
                    user_id=from_user_id,
                    amount=amount,
                    wallet_id=from_wallet.wallet_id,
                    transaction_id=sender_txn.txn_id,
                    additional_data={"to_user_id": to_user_id, "description": description}
                )
                
                FinancialAuditor.log_financial_operation(
                    operation_type="transfer_points_receive",
                    user_id=to_user_id,
                    amount=amount,
                    wallet_id=to_wallet.wallet_id,
                    transaction_id=receiver_txn.txn_id,
                    additional_data={"from_user_id": from_user_id, "description": description}
                )
                
                logger.info(f"Successfully transferred {amount} points from user {from_user_id} to {to_user_id}")
                return sender_txn, receiver_txn
                
            except Exception as e:
                logger.error(f"Failed to transfer points: {str(e)}")
                raise
    
    async def get_balance(self, user_id: int) -> WalletBalanceResponse:
        """
        Get current wallet balance and pending amounts
        
        Args:
            user_id: User ID
            
        Returns:
            WalletBalanceResponse with balance information
        """
        try:
            # Get wallet
            wallet = await self._get_or_create_wallet(user_id)
            
            # Calculate pending amounts
            pending_transactions = await self.transaction_service.get_pending_transactions(user_id)
            pending_amount = sum(
                abs(txn.amount) for txn in pending_transactions
                if txn.type == TransactionType.SPEND
            )
            
            return WalletBalanceResponse(
                wallet_id=wallet.wallet_id,
                user_id=user_id,
                balance=wallet.balance,
                pending_amount=pending_amount,
                available_balance=wallet.balance - pending_amount,
                last_updated=wallet.updated_at
            )
            
        except Exception as e:
            logger.error(f"Failed to get balance for user {user_id}: {str(e)}")
            raise
    
    async def get_transaction_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        transaction_type: Optional[TransactionType] = None,
        status_filter: Optional[TransactionStatus] = None
    ) -> TransactionHistoryResponse:
        """
        Get comprehensive transaction history for user
        
        Args:
            user_id: User ID
            limit: Number of transactions to return
            offset: Number of transactions to skip
            transaction_type: Optional transaction type filter
            status_filter: Optional status filter
            
        Returns:
            TransactionHistoryResponse with transactions and metadata
        """
        try:
            transactions, total_count = await self.transaction_service.get_user_transaction_history(
                user_id=user_id,
                limit=limit,
                offset=offset,
                transaction_type=transaction_type,
                status_filter=status_filter
            )
            
            # Convert to response objects
            transaction_responses = [
                TransactionResponse.model_validate(txn) for txn in transactions
            ]
            
            # Calculate summary metrics
            all_transactions, _ = await self.transaction_service.get_user_transaction_history(
                user_id=user_id,
                limit=1000,  # Get more for summary
                offset=0
            )
            
            summary = FinancialReporting.calculate_transaction_metrics(all_transactions)
            
            return TransactionHistoryResponse(
                transactions=transaction_responses,
                total_count=total_count,
                page_info={
                    "current_page": offset // limit + 1,
                    "page_size": limit,
                    "total_pages": (total_count + limit - 1) // limit,
                    "has_next": offset + limit < total_count,
                    "has_previous": offset > 0
                },
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Failed to get transaction history for user {user_id}: {str(e)}")
            raise
    
    # Internal helper methods
    async def _get_wallet_with_lock(self, user_id: int) -> Optional[Wallet]:
        """Get wallet with row-level locking"""
        result = await self.db.execute(
            select(Wallet)
            .where(Wallet.user_id == user_id)
            .with_for_update()  # Row-level lock
        )
        return result.scalar_one_or_none()
    
    async def _get_wallet_by_id_with_lock(self, wallet_id: int) -> Optional[Wallet]:
        """Get wallet by ID with row-level locking"""
        result = await self.db.execute(
            select(Wallet)
            .where(Wallet.wallet_id == wallet_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()
    
    async def _get_or_create_wallet(self, user_id: int) -> Wallet:
        """Get existing wallet or create new one"""
        # First try to get existing wallet
        result = await self.db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        wallet = result.scalar_one_or_none()

        if not wallet:
            # Create new wallet
            wallet = Wallet(user_id=user_id, balance=0)
            self.db.add(wallet)
            await self.db.flush()  # Get the wallet ID

            logger.info(f"Created new wallet {wallet.wallet_id} for user {user_id}")

        return wallet
    
    async def _get_recent_transactions(self, user_id: int, hours: int = 1) -> List[Transaction]:
        """Get recent transactions for user"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.db.execute(
            select(Transaction)
            .join(Wallet)
            .where(
                and_(
                    Wallet.user_id == user_id,
                    Transaction.created_at >= cutoff_time
                )
            )
            .order_by(Transaction.created_at.desc())
        )
        
        return result.scalars().all()
    
    async def admin_adjust_points(
        self,
        user_id: int,
        amount: int,
        reason: str,
        admin_user_id: int
    ) -> Transaction:
        """
        Admin function to adjust user points (positive or negative)
        
        Args:
            user_id: Target user ID
            amount: Points to adjust (positive = add, negative = deduct)
            reason: Reason for adjustment
            admin_user_id: ID of admin performing adjustment
            
        Returns:
            Transaction object
        """
        async with self.db.begin():
            try:
                # Validate inputs
                FinancialValidator.validate_user_id(user_id)
                if amount == 0:
                    raise FinancialValidationError("Adjustment amount cannot be zero")
                
                # Get or create wallet
                wallet = await self._get_or_create_wallet(user_id)
                
                # For negative adjustments, check if sufficient balance
                if amount < 0 and wallet.balance < abs(amount):
                    logger.warning(f"Admin deduction may result in negative balance for user {user_id}")
                
                # Determine transaction type
                transaction_type = TransactionType.DEPOSIT if amount > 0 else TransactionType.SPEND
                
                # Generate reference ID
                reference_id = f"admin_adj_{admin_user_id}_{int(datetime.utcnow().timestamp())}"
                
                # Create transaction
                transaction = await self.transaction_service.create_pending_transaction(
                    wallet_id=wallet.wallet_id,
                    transaction_type=transaction_type,
                    amount=amount,
                    reference_id=reference_id,
                    description=f"Admin adjustment by user {admin_user_id}: {reason}"
                )
                
                # Apply adjustment to wallet
                if amount > 0:
                    wallet.add_balance(amount)
                else:
                    wallet.balance += amount  # Direct assignment for admin operations
                
                # Complete transaction
                await self.transaction_service.complete_transaction(
                    transaction.txn_id,
                    TransactionStatus.SUCCESS
                )
                
                # Audit logging
                FinancialAuditor.log_financial_operation(
                    operation_type="admin_adjust_points",
                    user_id=user_id,
                    amount=abs(amount),
                    wallet_id=wallet.wallet_id,
                    transaction_id=transaction.txn_id,
                    reference_id=reference_id,
                    additional_data={
                        "admin_user_id": admin_user_id,
                        "reason": reason,
                        "adjustment_type": "credit" if amount > 0 else "debit"
                    }
                )
                
                logger.info(f"Admin {admin_user_id} adjusted {amount} points for user {user_id}: {reason}")
                return transaction
                
            except Exception as e:
                logger.error(f"Failed admin adjustment for user {user_id}: {str(e)}")
                raise


# Module-level utility functions for convenience
class WalletServiceUtils:
    """Utility functions for wallet operations without requiring service instantiation"""
    
    @staticmethod
    async def get_user_points(user_id: int, db: AsyncSession) -> int:
        """Get user's current point balance"""
        service = WalletService(db)
        balance_response = await service.get_balance(user_id)
        return balance_response.current_balance
    
    @staticmethod
    async def deduct_points(
        user_id: int,
        amount: int,
        db: AsyncSession,
        description: str = "Points deduction",
        reference_id: Optional[str] = None
    ) -> bool:
        """Deduct points from user's wallet"""
        try:
            service = WalletService(db)
            await service.spend_points(
                user_id=user_id,
                amount=amount,
                description=description,
                reference_id=reference_id
            )
            return True
        except InsufficientBalanceError:
            return False
        except Exception:
            return False


# Create a module-level instance for backward compatibility
wallet_service = WalletServiceUtils()