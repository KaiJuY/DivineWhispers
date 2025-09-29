"""
User wallet API endpoints
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database_session
from app.utils.deps import get_current_user
from app.models.user import User
from app.models.transaction import TransactionType, TransactionStatus
from app.services.wallet_service import WalletService
from app.schemas.wallet import (
    SpendPointsRequest,
    SpendPointsResponse,
    DepositPointsRequest,
    DepositPointsResponse,
    TransferPointsRequest,
    TransferResponse,
    TransactionHistoryQuery,
    TransactionHistoryResponse,
    WalletBalanceResponse,
    WalletResponse,
    TransactionResponse,
    InsufficientBalanceResponse,
    DuplicateTransactionResponse,
    WalletErrorResponse,
    TransactionTypeSchema,
    TransactionStatusSchema
)
from app.utils.financial import (
    InsufficientBalanceError,
    DuplicateTransactionError,
    FinancialValidationError,
    format_amount
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get current wallet balance and available points
    
    Returns:
        WalletBalanceResponse: Current balance, pending amounts, and available balance
    """
    try:
        wallet_service = WalletService(db)
        balance_info = await wallet_service.get_balance(current_user.user_id)
        
        logger.info(f"Balance retrieved for user {current_user.user_id}: {balance_info.balance} points")
        return balance_info
        
    except Exception as e:
        logger.error(f"Failed to get balance for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve wallet balance"
        )


@router.get("/transactions", response_model=TransactionHistoryResponse)
async def get_transaction_history(
    limit: int = Query(20, ge=1, le=100, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
    transaction_type: Optional[TransactionTypeSchema] = Query(None, description="Filter by transaction type"),
    status: Optional[TransactionStatusSchema] = Query(None, description="Filter by transaction status"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering (ISO format)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get transaction history with pagination and filtering
    
    Args:
        limit: Number of transactions to return (1-100)
        offset: Number of transactions to skip
        transaction_type: Filter by transaction type
        status: Filter by transaction status
        start_date: Start date for filtering
        end_date: End date for filtering
        
    Returns:
        TransactionHistoryResponse: Paginated transaction history with metadata
    """
    try:
        # Convert schema enums to model enums if provided
        model_transaction_type = None
        if transaction_type:
            model_transaction_type = TransactionType(transaction_type.value)
        
        model_status = None
        if status:
            model_status = TransactionStatus(status.value)
        
        wallet_service = WalletService(db)
        history = await wallet_service.get_transaction_history(
            user_id=current_user.user_id,
            limit=limit,
            offset=offset,
            transaction_type=model_transaction_type,
            status_filter=model_status
        )
        
        logger.info(f"Transaction history retrieved for user {current_user.user_id}: {len(history.transactions)} transactions")
        return history
        
    except Exception as e:
        logger.error(f"Failed to get transaction history for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction history"
        )


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_details(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get details of a specific transaction
    
    Args:
        transaction_id: Transaction ID to retrieve
        
    Returns:
        TransactionResponse: Transaction details
        
    Raises:
        HTTPException: If transaction not found or not owned by user
    """
    try:
        wallet_service = WalletService(db)
        transaction_service = wallet_service.transaction_service
        
        transaction = await transaction_service.get_transaction_by_id(transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction {transaction_id} not found"
            )
        
        # Check if transaction belongs to current user
        if transaction.wallet.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own transactions"
            )
        
        return TransactionResponse.model_validate(transaction)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transaction {transaction_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction details"
        )


@router.post("/spend", response_model=SpendPointsResponse)
async def spend_points(
    request: SpendPointsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Spend points for a service (creates job and deducts points atomically)
    
    Args:
        request: SpendPointsRequest with amount, job_type, and description
        
    Returns:
        SpendPointsResponse: Transaction details and remaining balance
        
    Raises:
        HTTPException: If insufficient balance or validation fails
    """
    try:
        wallet_service = WalletService(db)
        
        # Spend points and create job atomically
        transaction, job = await wallet_service.spend_points(
            user_id=current_user.user_id,
            amount=request.amount,
            job_type=request.job_type,
            description=request.description
        )
        
        # Get updated balance
        balance_info = await wallet_service.get_balance(current_user.user_id)
        
        response = SpendPointsResponse(
            transaction=TransactionResponse.model_validate(transaction),
            job_id=job.job_id,
            remaining_balance=balance_info.available_balance,
            message=f"Successfully spent {format_amount(request.amount)} for {request.job_type}"
        )
        
        logger.info(f"User {current_user.user_id} spent {request.amount} points for {request.job_type}")
        return response
        
    except InsufficientBalanceError as e:
        logger.warning(f"Insufficient balance for user {current_user.user_id}: {str(e)}")
        
        # Get current balance for error response
        try:
            balance_info = await wallet_service.get_balance(current_user.user_id)
            current_balance = balance_info.available_balance
        except:
            current_balance = 0
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=InsufficientBalanceResponse(
                error_message=str(e),
                current_balance=current_balance,
                required_amount=request.amount,
                shortfall=request.amount - current_balance
            ).dict()
        )
        
    except FinancialValidationError as e:
        logger.warning(f"Validation error for spend request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error(f"Failed to spend points for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process point spending"
        )


@router.post("/deposit", response_model=DepositPointsResponse)
async def deposit_points(
    request: DepositPointsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Deposit points to wallet (typically called after payment processing)
    
    Args:
        request: DepositPointsRequest with amount, reference_id, and description
        
    Returns:
        DepositPointsResponse: Transaction details and new balance
        
    Raises:
        HTTPException: If validation fails or duplicate transaction
    """
    try:
        wallet_service = WalletService(db)
        
        # Deposit points atomically
        transaction = await wallet_service.deposit_points(
            user_id=current_user.user_id,
            amount=request.amount,
            reference_id=request.reference_id,
            description=request.description
        )
        
        # Get updated balance
        balance_info = await wallet_service.get_balance(current_user.user_id)
        
        response = DepositPointsResponse(
            transaction=TransactionResponse.model_validate(transaction),
            new_balance=balance_info.balance,
            message=f"Successfully deposited {format_amount(request.amount)}"
        )
        
        logger.info(f"User {current_user.user_id} deposited {request.amount} points")
        return response
        
    except DuplicateTransactionError as e:
        logger.warning(f"Duplicate deposit attempt: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=DuplicateTransactionResponse(
                error_message=str(e),
                existing_transaction_id=0  # Would need to extract from error
            ).dict()
        )
        
    except FinancialValidationError as e:
        logger.warning(f"Validation error for deposit request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error(f"Failed to deposit points for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process point deposit"
        )


@router.post("/transfer", response_model=TransferResponse)
async def transfer_points(
    request: TransferPointsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Transfer points to another user
    
    Args:
        request: TransferPointsRequest with to_user_id, amount, and description
        
    Returns:
        TransferResponse: Both transaction details and updated balances
        
    Raises:
        HTTPException: If insufficient balance, invalid user, or validation fails
    """
    try:
        wallet_service = WalletService(db)
        
        # Transfer points atomically
        sender_txn, receiver_txn = await wallet_service.transfer_points(
            from_user_id=current_user.user_id,
            to_user_id=request.to_user_id,
            amount=request.amount,
            description=request.description
        )
        
        # Get updated balances
        sender_balance = await wallet_service.get_balance(current_user.user_id)
        receiver_balance = await wallet_service.get_balance(request.to_user_id)
        
        response = TransferResponse(
            sender_transaction=TransactionResponse.model_validate(sender_txn),
            receiver_transaction=TransactionResponse.model_validate(receiver_txn),
            sender_balance=sender_balance.available_balance,
            receiver_balance=receiver_balance.balance,
            message=f"Successfully transferred {format_amount(request.amount)} to user {request.to_user_id}"
        )
        
        logger.info(f"User {current_user.user_id} transferred {request.amount} points to user {request.to_user_id}")
        return response
        
    except InsufficientBalanceError as e:
        logger.warning(f"Insufficient balance for transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except FinancialValidationError as e:
        logger.warning(f"Validation error for transfer request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error(f"Failed to transfer points: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process point transfer"
        )


@router.get("/", response_model=WalletResponse)
async def get_wallet_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get complete wallet overview with balance and recent transactions
    
    Returns:
        WalletResponse: Complete wallet information
    """
    try:
        wallet_service = WalletService(db)
        
        # Get balance information
        balance_info = await wallet_service.get_balance(current_user.user_id)
        
        # Get recent transactions
        history = await wallet_service.get_transaction_history(
            user_id=current_user.user_id,
            limit=10,  # Recent transactions only
            offset=0
        )
        
        response = WalletResponse(
            wallet_id=balance_info.wallet_id,
            user_id=current_user.user_id,
            balance=balance_info.balance,
            pending_amount=balance_info.pending_amount,
            available_balance=balance_info.available_balance,
            last_updated=balance_info.last_updated,
            recent_transactions=history.transactions
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get wallet overview for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve wallet information"
        )


@router.get("/statistics")
async def get_wallet_statistics(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get wallet usage statistics
    
    Args:
        days_back: Number of days to analyze (1-365)
        
    Returns:
        Dictionary containing wallet usage statistics
    """
    try:
        wallet_service = WalletService(db)
        
        # Get transaction statistics
        stats = await wallet_service.transaction_service.get_transaction_statistics(
            user_id=current_user.user_id,
            days_back=days_back
        )
        
        # Add current balance
        balance_info = await wallet_service.get_balance(current_user.user_id)
        stats["current_balance"] = balance_info.balance
        stats["available_balance"] = balance_info.available_balance
        stats["pending_amount"] = balance_info.pending_amount
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get wallet statistics for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve wallet statistics"
        )


# Health check endpoint for wallet service
@router.get("/health")
async def wallet_health_check(
    db: AsyncSession = Depends(get_database_session)
):
    """
    Health check for wallet service functionality
    
    Returns:
        Dictionary containing health status
    """
    try:
        wallet_service = WalletService(db)
        
        # Check transaction integrity
        integrity_check = await wallet_service.transaction_service.validate_transaction_integrity()
        
        return {
            "status": "healthy" if integrity_check["is_healthy"] else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "integrity_check": integrity_check
        }
        
    except Exception as e:
        logger.error(f"Wallet health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Coin Purchase System

@router.get("/packages")
async def get_coin_packages():
    """Get available coin purchase packages"""
    packages = [
        {
            "id": "starter_pack",
            "name": "Starter Pack",
            "coins": 5,
            "price_usd": 1.5,
            "bonus_coins": 0,
            "description": "Perfect for trying out fortune readings",
            "popular": False
        },
        {
            "id": "value_pack", 
            "name": "Value Pack",
            "coins": 25,
            "price_usd": 7.5,
            "bonus_coins": 5,
            "description": "Most popular choice with bonus coins",
            "popular": True
        },
        {
            "id": "premium_pack",
            "name": "Premium Pack", 
            "coins": 100,
            "price_usd": 30,
            "bonus_coins": 50,
            "description": "Best value for frequent users",
            "popular": False
        }
    ]
    
    return {
        "packages": packages,
        "currency": "USD",
        "payment_methods": ["card", "paypal", "apple-pay", "google-pay"]
    }


@router.post("/purchase")
async def initiate_coin_purchase(
    package_id: str,
    payment_method: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """Initiate coin package purchase"""
    try:
        # Get package details
        packages_response = await get_coin_packages()
        package = next((p for p in packages_response["packages"] if p["id"] == package_id), None)
        
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        if payment_method not in packages_response["payment_methods"]:
            raise HTTPException(status_code=400, detail="Invalid payment method")
        
        # Create pending purchase record (placeholder)
        purchase_id = f"purchase_{current_user.user_id}_{datetime.utcnow().timestamp()}"
        
        # In a real implementation, you would:
        # 1. Create payment session with Stripe/PayPal
        # 2. Store purchase intent in database
        # 3. Return payment URL/token for frontend
        
        return {
            "purchase_id": purchase_id,
            "package": package,
            "payment_method": payment_method,
            "total_amount": package["price_usd"],
            "status": "pending",
            # Mock payment URL for testing
            "payment_url": f"https://mock-payment.example.com/pay/{purchase_id}",
            "expires_at": (datetime.utcnow().timestamp() + 1800),  # 30 minutes
            "message": "Please complete payment to receive your coins"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating purchase for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate purchase")


@router.post("/purchase/{purchase_id}/complete")
async def complete_coin_purchase(
    purchase_id: str,
    payment_confirmation: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """Complete coin purchase after successful payment"""
    try:
        # In a real implementation, you would:
        # 1. Verify payment with payment provider
        # 2. Check purchase record exists and belongs to user
        # 3. Add coins to user wallet
        # 4. Create transaction record
        
        # Mock successful purchase completion
        wallet_service = WalletService(db)
        
        # For demo purposes, assume successful payment for 120 coins (Value Pack)
        coins_purchased = 120
        bonus_coins = 20
        total_coins = coins_purchased + bonus_coins
        
        # Add coins to wallet
        transaction = await wallet_service.credit_points(
            user_id=current_user.user_id,
            amount=total_coins,
            description=f"Coin purchase: {coins_purchased} + {bonus_coins} bonus",
            transaction_metadata={
                "purchase_id": purchase_id,
                "payment_method": payment_confirmation.get("method", "credit_card"),
                "package_type": "value_pack"
            }
        )
        
        # Get updated balance
        balance_info = await wallet_service.get_balance(current_user.user_id)
        
        logger.info(f"Successfully completed coin purchase for user {current_user.user_id}: +{total_coins} coins")
        
        return {
            "purchase_id": purchase_id,
            "status": "completed",
            "coins_added": total_coins,
            "breakdown": {
                "purchased": coins_purchased,
                "bonus": bonus_coins
            },
            "new_balance": balance_info.available_balance,
            "transaction_id": transaction.transaction_id,
            "message": f"Successfully added {total_coins} coins to your account!"
        }
        
    except Exception as e:
        logger.error(f"Error completing purchase {purchase_id} for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete purchase")


@router.get("/purchases")
async def get_purchase_history(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """Get user's coin purchase history"""
    try:
        wallet_service = WalletService(db)

        # Get credit transactions (purchases)
        from app.models.transaction import TransactionType
        try:
            transactions = await wallet_service.get_transaction_history(
                user_id=current_user.user_id,
                transaction_type=TransactionType.DEPOSIT,  # DEPOSIT transactions are credits/purchases
                limit=limit,
                offset=offset
            )
        except Exception as wallet_error:
            # If user has no wallet or no transactions, return empty array
            logger.info(f"No wallet/transactions found for user {current_user.user_id}: {wallet_error}")
            return {
                "purchases": [],
                "total_count": 0,
                "has_more": False
            }

        purchases = []
        if transactions and hasattr(transactions, 'transactions') and transactions.transactions:
            for transaction in transactions.transactions:
                # Check if transaction looks like a purchase (has purchase in description)
                description = getattr(transaction, 'description', '') or ''
                if "purchase" in description.lower() or "coin" in description.lower():
                    # Handle metadata safely
                    metadata = getattr(transaction, 'metadata', {}) or {}
                    purchases.append({
                        "purchase_id": metadata.get("purchase_id", f"legacy_{getattr(transaction, 'transaction_id', transaction.txn_id)}"),
                        "amount": getattr(transaction, 'amount', 0),
                        "description": description,
                        "payment_method": metadata.get("payment_method", "unknown"),
                        "package_type": metadata.get("package_type", "unknown"),
                        "created_at": getattr(transaction, 'created_at', None),
                        "status": "completed"
                    })

        return {
            "purchases": purchases,
            "total_count": len(purchases),
            "has_more": transactions and hasattr(transactions, 'transactions') and len(transactions.transactions) == limit
        }
        
    except Exception as e:
        logger.error(f"Error getting purchase history for user {current_user.user_id}: {e}")
        # Return empty array instead of 500 error for better user experience
        return {
            "purchases": [],
            "total_count": 0,
            "has_more": False
        }