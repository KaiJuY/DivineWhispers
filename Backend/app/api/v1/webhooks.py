"""
Webhook API endpoints for payment providers

Handles webhooks from:
- Stripe (US/Japan payments)
- TapPay (Taiwan payments)

Implements secure webhook verification and payment processing
according to the Phase 2 payment strategy plan.
"""

import logging
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database_session
from app.services.payment_service import PaymentService
from app.services.wallet_service import WalletService
from app.services.payment_strategies.base import PaymentProvider, PaymentStatus
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize payment service (would be configured from environment variables)
PAYMENT_CONFIG = {
    "stripe": {
        "api_key": getattr(settings, "STRIPE_SECRET_KEY", "sk_test_..."),
        "webhook_secret": getattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_..."),
        "publishable_key": getattr(settings, "STRIPE_PUBLISHABLE_KEY", "pk_test_...")
    },
    "tappay": {
        "partner_key": getattr(settings, "TAPPAY_PARTNER_KEY", "partner_key_..."),
        "merchant_id": getattr(settings, "TAPPAY_MERCHANT_ID", "merchant_id_..."),
        "app_id": getattr(settings, "TAPPAY_APP_ID", "app_id_..."),
        "app_key": getattr(settings, "TAPPAY_APP_KEY", "app_key_..."),
        "is_sandbox": getattr(settings, "TAPPAY_SANDBOX", True)
    }
}

try:
    payment_service = PaymentService(PAYMENT_CONFIG)
except Exception as e:
    logger.warning(f"Could not initialize payment service: {e}")
    payment_service = None


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Handle Stripe webhook events

    Processes payment_intent.succeeded and payment_intent.payment_failed events
    to update user wallet balances and transaction records.
    """
    if not payment_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service not available"
        )

    try:
        # Get raw payload and signature
        payload = await request.body()
        signature = request.headers.get("stripe-signature")

        if not signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature"
            )

        # Process webhook with payment service
        payment_result = await payment_service.handle_webhook(
            provider=PaymentProvider.STRIPE,
            payload=payload,
            signature=signature
        )

        if not payment_result:
            # Webhook was invalid or not a payment event we care about
            return JSONResponse({"status": "ignored"})

        # Process the payment result
        await process_payment_result(payment_result, db)

        logger.info(f"Processed Stripe webhook for payment {payment_result.payment_id}")
        return JSONResponse({"status": "success"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


@router.post("/tappay")
async def tappay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Handle TapPay webhook events

    Processes TapPay payment notifications to update user wallet
    balances and transaction records for Taiwan users.
    """
    if not payment_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service not available"
        )

    try:
        # Get raw payload and signature
        payload = await request.body()
        signature = request.headers.get("x-tappay-signature", "")

        # Process webhook with payment service
        payment_result = await payment_service.handle_webhook(
            provider=PaymentProvider.TAPPAY,
            payload=payload,
            signature=signature
        )

        if not payment_result:
            # Webhook was invalid or not a payment event we care about
            return JSONResponse({"status": "ignored"})

        # Process the payment result
        await process_payment_result(payment_result, db)

        logger.info(f"Processed TapPay webhook for payment {payment_result.payment_id}")
        return JSONResponse({"status": "success"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing TapPay webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


async def process_payment_result(payment_result, db: AsyncSession):
    """
    Process payment result and update wallet balance

    Args:
        payment_result: PaymentResult from webhook processing
        db: Database session
    """
    try:
        # Extract user ID from payment metadata
        user_id = None
        if payment_result.metadata:
            user_id = payment_result.metadata.get("user_id")

        if not user_id:
            logger.error(f"No user_id in payment metadata for {payment_result.payment_id}")
            return

        user_id = int(user_id)

        # Initialize wallet service
        wallet_service = WalletService(db)

        if payment_result.success and payment_result.status == PaymentStatus.SUCCESS:
            # Payment succeeded - credit user wallet
            package_id = payment_result.metadata.get("package_id", "unknown")

            # Calculate coins based on amount (this would be more sophisticated in production)
            # For now, assume 1 coin per $0.10 USD or equivalent
            coins_to_add = payment_result.amount // 10  # Convert cents to coins

            # Create credit transaction (deposit) with reference id for idempotency
            transaction = await wallet_service.deposit_points(
                user_id=user_id,
                amount=coins_to_add,
                reference_id=payment_result.payment_id,
                description=f"Coin purchase via {payment_result.provider.value}: {package_id}"
            )

            logger.info(
                f"Credited {coins_to_add} coins to user {user_id} "
                f"for payment {payment_result.payment_id}"
            )

        elif payment_result.status == PaymentStatus.FAILED:
            # Payment failed - log for monitoring
            logger.warning(
                f"Payment {payment_result.payment_id} failed for user {user_id}: "
                f"{payment_result.error_message}"
            )

            # Could create a failed transaction record here for audit purposes

    except Exception as e:
        logger.error(f"Error processing payment result: {e}")
        raise


@router.get("/health")
async def webhook_health():
    """
    Health check endpoint for webhook service
    """
    health_status = {
        "service": "webhook_handler",
        "status": "healthy",
        "payment_service_available": payment_service is not None
    }

    if payment_service:
        health_status["available_providers"] = [
            provider.value for provider in payment_service.get_available_providers()
        ]

    return health_status
