"""
Base Payment Strategy Interface for multi-market payment processing

Supports Taiwan (TapPay) and US/Japan (Stripe) payment flows
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class PaymentStatus(Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REQUIRES_ACTION = "requires_action"  # For 3D Secure


class PaymentProvider(Enum):
    """Payment provider enumeration"""
    STRIPE = "stripe"
    TAPPAY = "tappay"


@dataclass
class PaymentIntent:
    """Payment intent data structure"""
    intent_id: str
    amount: int  # Amount in cents
    currency: str
    provider: PaymentProvider
    client_secret: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: PaymentStatus = PaymentStatus.PENDING


@dataclass
class PaymentResult:
    """Payment processing result"""
    success: bool
    payment_id: str
    status: PaymentStatus
    amount: int
    currency: str
    provider: PaymentProvider
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentStrategy(ABC):
    """
    Abstract base class for payment strategies

    Each payment provider (TapPay, Stripe) implements this interface
    to provide consistent payment processing across different markets
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize payment strategy with configuration

        Args:
            config: Provider-specific configuration (API keys, etc.)
        """
        self.config = config
        self.provider = self._get_provider()

    @abstractmethod
    def _get_provider(self) -> PaymentProvider:
        """Return the payment provider enum for this strategy"""
        pass

    @abstractmethod
    async def create_payment_intent(
        self,
        amount: int,
        currency: str,
        user_id: int,
        package_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentIntent:
        """
        Create a payment intent/session

        Args:
            amount: Amount in cents (e.g., 999 for $9.99)
            currency: Currency code (USD, TWD, JPY)
            user_id: User identifier
            package_id: Coin package identifier
            metadata: Additional metadata for the payment

        Returns:
            PaymentIntent object with provider-specific details
        """
        pass

    @abstractmethod
    async def verify_payment(self, payment_id: str) -> PaymentResult:
        """
        Verify a payment status with the provider

        Args:
            payment_id: Provider-specific payment identifier

        Returns:
            PaymentResult with verification details
        """
        pass

    @abstractmethod
    async def handle_webhook(self, payload: bytes, signature: str) -> Optional[PaymentResult]:
        """
        Handle webhook notification from payment provider

        Args:
            payload: Raw webhook payload
            signature: Webhook signature for verification

        Returns:
            PaymentResult if webhook is valid, None if invalid/ignored
        """
        pass

    @abstractmethod
    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Validate webhook signature

        Args:
            payload: Raw webhook payload
            signature: Signature to validate

        Returns:
            True if signature is valid
        """
        pass

    def get_supported_currencies(self) -> list[str]:
        """
        Get list of supported currencies for this provider

        Returns:
            List of currency codes
        """
        # Default implementation - override in subclasses
        return ["USD"]

    def get_provider_name(self) -> str:
        """Get human-readable provider name"""
        return self.provider.value.title()

    def format_amount(self, amount: int, currency: str) -> str:
        """
        Format amount for display

        Args:
            amount: Amount in cents
            currency: Currency code

        Returns:
            Formatted amount string
        """
        if currency == "USD":
            return f"${amount / 100:.2f}"
        elif currency == "TWD":
            return f"NT${amount}"
        elif currency == "JPY":
            return f"¥{amount}"
        else:
            return f"{amount / 100:.2f} {currency}"