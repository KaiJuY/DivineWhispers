"""
Stripe Payment Strategy for US and Japan markets

Handles credit card payments through Stripe with support for:
- USD (United States)
- JPY (Japan)
- 3D Secure authentication
- Apple Pay and Google Pay (future)
"""

import logging
import stripe
from typing import Dict, Any, Optional
from .base import PaymentStrategy, PaymentIntent, PaymentResult, PaymentStatus, PaymentProvider

logger = logging.getLogger(__name__)


class StripeCreditCardStrategy(PaymentStrategy):
    """
    Stripe payment strategy for credit card processing

    Supports US (USD) and Japan (JPY) markets with automatic
    3D Secure handling for fraud protection
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Stripe strategy

        Expected config:
        {
            "api_key": "sk_test_...",
            "webhook_secret": "whsec_...",
            "publishable_key": "pk_test_..."
        }
        """
        super().__init__(config)

        # Configure Stripe SDK
        stripe.api_key = config.get("api_key")
        self.webhook_secret = config.get("webhook_secret")
        self.publishable_key = config.get("publishable_key")

        if not stripe.api_key:
            raise ValueError("Stripe API key is required")

    def _get_provider(self) -> PaymentProvider:
        """Return Stripe provider enum"""
        return PaymentProvider.STRIPE

    async def create_payment_intent(
        self,
        amount: int,
        currency: str,
        user_id: int,
        package_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentIntent:
        """
        Create Stripe PaymentIntent for credit card processing

        Args:
            amount: Amount in cents (e.g., 999 for $9.99)
            currency: Currency code (USD, JPY)
            user_id: User identifier
            package_id: Coin package identifier
            metadata: Additional metadata

        Returns:
            PaymentIntent with Stripe-specific client_secret
        """
        try:
            # Validate currency support
            if currency.upper() not in self.get_supported_currencies():
                raise ValueError(f"Currency {currency} not supported by Stripe")

            # Prepare metadata
            payment_metadata = {
                "user_id": str(user_id),
                "package_id": package_id,
                "provider": "stripe"
            }
            if metadata:
                payment_metadata.update(metadata)

            # Create Stripe PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency.lower(),
                metadata=payment_metadata,
                automatic_payment_methods={
                    "enabled": True,
                },
                # Enable 3D Secure for fraud protection
                confirmation_method="automatic"
            )

            logger.info(f"Created Stripe PaymentIntent {intent.id} for user {user_id}")

            return PaymentIntent(
                intent_id=intent.id,
                amount=amount,
                currency=currency.upper(),
                provider=PaymentProvider.STRIPE,
                client_secret=intent.client_secret,
                metadata=payment_metadata,
                status=PaymentStatus.PENDING
            )

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating PaymentIntent: {e}")
            raise Exception(f"Failed to create payment intent: {e.user_message or str(e)}")
        except Exception as e:
            logger.error(f"Error creating Stripe PaymentIntent: {e}")
            raise Exception(f"Failed to create payment intent: {str(e)}")

    async def verify_payment(self, payment_id: str) -> PaymentResult:
        """
        Verify Stripe payment status

        Args:
            payment_id: Stripe PaymentIntent ID

        Returns:
            PaymentResult with verification details
        """
        try:
            # Retrieve PaymentIntent from Stripe
            intent = stripe.PaymentIntent.retrieve(payment_id)

            # Map Stripe status to our PaymentStatus
            status_mapping = {
                "requires_payment_method": PaymentStatus.PENDING,
                "requires_confirmation": PaymentStatus.PENDING,
                "requires_action": PaymentStatus.REQUIRES_ACTION,
                "processing": PaymentStatus.PENDING,
                "requires_capture": PaymentStatus.SUCCESS,  # Auto-capture enabled
                "succeeded": PaymentStatus.SUCCESS,
                "canceled": PaymentStatus.CANCELLED
            }

            status = status_mapping.get(intent.status, PaymentStatus.FAILED)
            success = status == PaymentStatus.SUCCESS

            # Get charge ID if available
            transaction_id = None
            if intent.charges and intent.charges.data:
                transaction_id = intent.charges.data[0].id

            logger.info(f"Verified Stripe payment {payment_id}: {intent.status}")

            return PaymentResult(
                success=success,
                payment_id=payment_id,
                status=status,
                amount=intent.amount,
                currency=intent.currency.upper(),
                provider=PaymentProvider.STRIPE,
                transaction_id=transaction_id,
                metadata=intent.metadata
            )

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error verifying payment {payment_id}: {e}")
            return PaymentResult(
                success=False,
                payment_id=payment_id,
                status=PaymentStatus.FAILED,
                amount=0,
                currency="USD",
                provider=PaymentProvider.STRIPE,
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Error verifying Stripe payment {payment_id}: {e}")
            return PaymentResult(
                success=False,
                payment_id=payment_id,
                status=PaymentStatus.FAILED,
                amount=0,
                currency="USD",
                provider=PaymentProvider.STRIPE,
                error_message=str(e)
            )

    async def handle_webhook(self, payload: bytes, signature: str) -> Optional[PaymentResult]:
        """
        Handle Stripe webhook events

        Args:
            payload: Raw webhook payload
            signature: Stripe signature header

        Returns:
            PaymentResult for payment_intent events, None for others
        """
        try:
            # Verify webhook signature
            if not self.validate_webhook_signature(payload, signature):
                logger.warning("Invalid Stripe webhook signature")
                return None

            # Parse webhook event
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )

            logger.info(f"Received Stripe webhook: {event['type']}")

            # Handle payment_intent events
            if event["type"] == "payment_intent.succeeded":
                intent = event["data"]["object"]

                # Get charge ID
                transaction_id = None
                if "charges" in intent and intent["charges"]["data"]:
                    transaction_id = intent["charges"]["data"][0]["id"]

                return PaymentResult(
                    success=True,
                    payment_id=intent["id"],
                    status=PaymentStatus.SUCCESS,
                    amount=intent["amount"],
                    currency=intent["currency"].upper(),
                    provider=PaymentProvider.STRIPE,
                    transaction_id=transaction_id,
                    metadata=intent.get("metadata", {})
                )

            elif event["type"] == "payment_intent.payment_failed":
                intent = event["data"]["object"]

                return PaymentResult(
                    success=False,
                    payment_id=intent["id"],
                    status=PaymentStatus.FAILED,
                    amount=intent["amount"],
                    currency=intent["currency"].upper(),
                    provider=PaymentProvider.STRIPE,
                    error_message=intent.get("last_payment_error", {}).get("message"),
                    metadata=intent.get("metadata", {})
                )

            # Ignore other event types
            return None

        except stripe.error.SignatureVerificationError:
            logger.warning("Invalid Stripe webhook signature")
            return None
        except Exception as e:
            logger.error(f"Error handling Stripe webhook: {e}")
            return None

    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Validate Stripe webhook signature

        Args:
            payload: Raw webhook payload
            signature: Stripe signature header

        Returns:
            True if signature is valid
        """
        try:
            stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return True
        except stripe.error.SignatureVerificationError:
            return False
        except Exception:
            return False

    def get_supported_currencies(self) -> list[str]:
        """
        Get currencies supported by Stripe strategy

        Returns:
            List of supported currency codes
        """
        return ["USD", "JPY"]

    def get_public_key(self) -> str:
        """
        Get Stripe publishable key for frontend

        Returns:
            Stripe publishable key
        """
        return self.publishable_key or ""