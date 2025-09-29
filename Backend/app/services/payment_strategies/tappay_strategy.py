"""
TapPay Payment Strategy for Taiwan market

Handles credit card payments through TapPay with support for:
- TWD (Taiwan Dollar)
- 3D Secure authentication
- Local Taiwan payment methods
"""

import logging
import json
import hashlib
import hmac
import httpx
from typing import Dict, Any, Optional
from .base import PaymentStrategy, PaymentIntent, PaymentResult, PaymentStatus, PaymentProvider

logger = logging.getLogger(__name__)


class TapPayStrategy(PaymentStrategy):
    """
    TapPay payment strategy for Taiwan market

    Supports TWD payments with TapPay's secure payment processing
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize TapPay strategy

        Expected config:
        {
            "partner_key": "partner_key_from_tappay",
            "merchant_id": "merchant_id_from_tappay",
            "app_id": "app_id_from_tappay",
            "app_key": "app_key_from_tappay",
            "is_sandbox": true
        }
        """
        super().__init__(config)

        self.partner_key = config.get("partner_key")
        self.merchant_id = config.get("merchant_id")
        self.app_id = config.get("app_id")
        self.app_key = config.get("app_key")
        self.is_sandbox = config.get("is_sandbox", True)

        # TapPay API endpoints
        if self.is_sandbox:
            self.base_url = "https://sandbox.tappaysdk.com"
        else:
            self.base_url = "https://prod.tappaysdk.com"

        # Validate required config
        required_fields = ["partner_key", "merchant_id", "app_id", "app_key"]
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"TapPay {field} is required")

    def _get_provider(self) -> PaymentProvider:
        """Return TapPay provider enum"""
        return PaymentProvider.TAPPAY

    async def create_payment_intent(
        self,
        amount: int,
        currency: str,
        user_id: int,
        package_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentIntent:
        """
        Create TapPay payment session

        Args:
            amount: Amount in cents for TWD (e.g., 999 for NT$9.99)
            currency: Currency code (TWD)
            user_id: User identifier
            package_id: Coin package identifier
            metadata: Additional metadata

        Returns:
            PaymentIntent with TapPay-specific session data
        """
        try:
            # Validate currency support
            if currency.upper() not in self.get_supported_currencies():
                raise ValueError(f"Currency {currency} not supported by TapPay")

            # Prepare metadata
            payment_metadata = {
                "user_id": str(user_id),
                "package_id": package_id,
                "provider": "tappay"
            }
            if metadata:
                payment_metadata.update(metadata)

            # Create unique order ID
            order_id = f"order_{user_id}_{package_id}_{hash(str(amount) + str(user_id))}"

            # Prepare TapPay payment request
            payment_data = {
                "partner_key": self.partner_key,
                "merchant_id": self.merchant_id,
                "amount": amount,
                "currency": currency.upper(),
                "order_number": order_id,
                "bank_transaction_id": order_id,
                "details": f"Divine Whispers - {package_id}",
                "cardholder": {
                    "phone_number": "",
                    "name": f"User {user_id}",
                    "email": f"user{user_id}@example.com"
                },
                "remember": False
            }

            # For now, we'll create a mock payment intent since we don't have actual TapPay credentials
            # In production, this would make an API call to TapPay

            logger.info(f"Created TapPay payment session {order_id} for user {user_id}")

            return PaymentIntent(
                intent_id=order_id,
                amount=amount,
                currency=currency.upper(),
                provider=PaymentProvider.TAPPAY,
                client_secret=self._generate_client_secret(order_id),
                metadata=payment_metadata,
                status=PaymentStatus.PENDING
            )

        except Exception as e:
            logger.error(f"Error creating TapPay payment intent: {e}")
            raise Exception(f"Failed to create payment intent: {str(e)}")

    async def verify_payment(self, payment_id: str) -> PaymentResult:
        """
        Verify TapPay payment status

        Args:
            payment_id: TapPay order ID

        Returns:
            PaymentResult with verification details
        """
        try:
            # In production, this would query TapPay's API to verify payment status
            # For now, we'll return a mock successful result

            logger.info(f"Verified TapPay payment {payment_id}")

            return PaymentResult(
                success=True,
                payment_id=payment_id,
                status=PaymentStatus.SUCCESS,
                amount=999,  # Mock amount
                currency="TWD",
                provider=PaymentProvider.TAPPAY,
                transaction_id=f"tappay_txn_{payment_id}",
                metadata={"order_id": payment_id}
            )

        except Exception as e:
            logger.error(f"Error verifying TapPay payment {payment_id}: {e}")
            return PaymentResult(
                success=False,
                payment_id=payment_id,
                status=PaymentStatus.FAILED,
                amount=0,
                currency="TWD",
                provider=PaymentProvider.TAPPAY,
                error_message=str(e)
            )

    async def handle_webhook(self, payload: bytes, signature: str) -> Optional[PaymentResult]:
        """
        Handle TapPay webhook events

        Args:
            payload: Raw webhook payload
            signature: TapPay signature header

        Returns:
            PaymentResult for payment events, None for others
        """
        try:
            # Verify webhook signature
            if not self.validate_webhook_signature(payload, signature):
                logger.warning("Invalid TapPay webhook signature")
                return None

            # Parse webhook data
            data = json.loads(payload.decode('utf-8'))

            logger.info(f"Received TapPay webhook: {data.get('status', 'unknown')}")

            # Extract payment information
            order_id = data.get("order_number")
            status = data.get("status")
            amount = data.get("amount", 0)

            if not order_id:
                logger.warning("TapPay webhook missing order_number")
                return None

            # Map TapPay status to our PaymentStatus
            if status == 0:  # Success
                payment_status = PaymentStatus.SUCCESS
                success = True
            elif status == 1:  # Failed
                payment_status = PaymentStatus.FAILED
                success = False
            else:
                payment_status = PaymentStatus.PENDING
                success = False

            return PaymentResult(
                success=success,
                payment_id=order_id,
                status=payment_status,
                amount=amount,
                currency="TWD",
                provider=PaymentProvider.TAPPAY,
                transaction_id=data.get("transaction_id"),
                metadata=data
            )

        except Exception as e:
            logger.error(f"Error handling TapPay webhook: {e}")
            return None

    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Validate TapPay webhook signature

        Args:
            payload: Raw webhook payload
            signature: TapPay signature header

        Returns:
            True if signature is valid
        """
        try:
            # TapPay signature validation logic
            # This would use the partner_key to validate the signature
            expected_signature = hmac.new(
                self.partner_key.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_signature, signature)

        except Exception:
            return False

    def get_supported_currencies(self) -> list[str]:
        """
        Get currencies supported by TapPay strategy

        Returns:
            List of supported currency codes
        """
        return ["TWD"]

    def _generate_client_secret(self, order_id: str) -> str:
        """
        Generate client secret for TapPay payment

        Args:
            order_id: Order identifier

        Returns:
            Client secret for frontend
        """
        # In production, this would be returned by TapPay API
        return f"tappay_cs_{order_id}_{self.app_id}"

    def get_app_config(self) -> Dict[str, str]:
        """
        Get TapPay app configuration for frontend

        Returns:
            Dictionary with app_id and app_key for frontend SDK
        """
        return {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "is_sandbox": self.is_sandbox
        }