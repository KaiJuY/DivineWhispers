"""
Payment Service with Strategy Pattern for Multi-Market Support

Automatically selects appropriate payment provider based on user location:
- Taiwan users: TapPay (TWD)
- US/Japan users: Stripe (USD/JPY)

Implements Phase 2 of the Purchase.md plan with credit card only support.
"""

import logging
from typing import Dict, Any, Optional
from app.models.user import User
from app.services.payment_strategies import (
    PaymentStrategy,
    PaymentIntent,
    PaymentResult,
    PaymentProvider,
    StripeCreditCardStrategy,
    TapPayStrategy
)

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Main payment service that manages multiple payment strategies

    Provides unified interface for payment processing across different
    markets and automatically selects the appropriate provider.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize payment service with multi-provider configuration

        Expected config structure:
        {
            "stripe": {
                "api_key": "sk_test_...",
                "webhook_secret": "whsec_...",
                "publishable_key": "pk_test_..."
            },
            "tappay": {
                "partner_key": "partner_key_...",
                "merchant_id": "merchant_id_...",
                "app_id": "app_id_...",
                "app_key": "app_key_...",
                "is_sandbox": true
            }
        }
        """
        self.config = config
        self.strategies: Dict[PaymentProvider, PaymentStrategy] = {}

        # Initialize available payment strategies
        self._initialize_strategies()

    def _initialize_strategies(self):
        """Initialize payment strategies based on configuration"""
        try:
            # Initialize Stripe strategy for US/Japan
            if "stripe" in self.config:
                self.strategies[PaymentProvider.STRIPE] = StripeCreditCardStrategy(
                    self.config["stripe"]
                )
                logger.info("Initialized Stripe payment strategy")

            # Initialize TapPay strategy for Taiwan
            if "tappay" in self.config:
                self.strategies[PaymentProvider.TAPPAY] = TapPayStrategy(
                    self.config["tappay"]
                )
                logger.info("Initialized TapPay payment strategy")

            if not self.strategies:
                logger.warning("No payment strategies initialized")

        except Exception as e:
            logger.error(f"Error initializing payment strategies: {e}")
            raise

    def get_strategy_for_user(self, user: User) -> PaymentStrategy:
        """
        Select appropriate payment strategy based on user location

        Args:
            user: User object with location information

        Returns:
            PaymentStrategy instance for the user's region

        Raises:
            ValueError: If no suitable strategy is found
        """
        # Determine user's country/locale
        user_country = self._get_user_country(user)

        logger.info(f"Selecting payment strategy for user {user.user_id} in {user_country}")

        # Strategy selection logic based on Purchase.md plan
        if user_country in ["TW", "Taiwan"]:
            # Taiwan users -> TapPay
            if PaymentProvider.TAPPAY in self.strategies:
                return self.strategies[PaymentProvider.TAPPAY]
            else:
                raise ValueError("TapPay strategy not available for Taiwan user")

        elif user_country in ["US", "United States", "JP", "Japan"]:
            # US/Japan users -> Stripe
            if PaymentProvider.STRIPE in self.strategies:
                return self.strategies[PaymentProvider.STRIPE]
            else:
                raise ValueError("Stripe strategy not available for US/Japan user")

        else:
            # Default to Stripe for other regions
            if PaymentProvider.STRIPE in self.strategies:
                logger.info(f"Using Stripe as default for country {user_country}")
                return self.strategies[PaymentProvider.STRIPE]
            else:
                raise ValueError(f"No payment strategy available for country {user_country}")

    def _get_user_country(self, user: User) -> str:
        """
        Extract user's country from user object

        Args:
            user: User object

        Returns:
            Country code or name
        """
        # Check user location field
        if hasattr(user, 'location') and user.location:
            location = user.location.upper()
            # Map location strings to countries
            if "TAIWAN" in location or "TW" in location:
                return "TW"
            elif "USA" in location or "UNITED STATES" in location or "US" in location:
                return "US"
            elif "JAPAN" in location or "JP" in location:
                return "JP"

        # Default to US if location is not specified
        logger.info(f"Could not determine country for user {user.user_id}, defaulting to US")
        return "US"

    async def create_payment_intent(
        self,
        user: User,
        amount: int,
        currency: str,
        package_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentIntent:
        """
        Create payment intent using appropriate strategy

        Args:
            user: User making the payment
            amount: Amount in cents/minor currency units
            currency: Currency code (USD, TWD, JPY)
            package_id: Coin package identifier
            metadata: Additional metadata

        Returns:
            PaymentIntent from the selected strategy
        """
        strategy = self.get_strategy_for_user(user)

        return await strategy.create_payment_intent(
            amount=amount,
            currency=currency,
            user_id=user.user_id,
            package_id=package_id,
            metadata=metadata
        )

    async def verify_payment(
        self,
        user: User,
        payment_id: str
    ) -> PaymentResult:
        """
        Verify payment using appropriate strategy

        Args:
            user: User who made the payment
            payment_id: Payment identifier

        Returns:
            PaymentResult from the selected strategy
        """
        strategy = self.get_strategy_for_user(user)

        return await strategy.verify_payment(payment_id)

    async def handle_webhook(
        self,
        provider: PaymentProvider,
        payload: bytes,
        signature: str
    ) -> Optional[PaymentResult]:
        """
        Handle webhook from specific payment provider

        Args:
            provider: Payment provider enum
            payload: Raw webhook payload
            signature: Webhook signature

        Returns:
            PaymentResult if webhook is valid, None otherwise
        """
        if provider not in self.strategies:
            logger.warning(f"No strategy available for provider {provider}")
            return None

        strategy = self.strategies[provider]
        return await strategy.handle_webhook(payload, signature)

    def get_frontend_config(self, user: User) -> Dict[str, Any]:
        """
        Get frontend configuration for the user's payment strategy

        Args:
            user: User object

        Returns:
            Configuration dict for frontend payment integration
        """
        strategy = self.get_strategy_for_user(user)
        user_country = self._get_user_country(user)

        config = {
            "provider": strategy.provider.value,
            "country": user_country,
            "supported_currencies": strategy.get_supported_currencies(),
            "enabled_methods": ["credit_card"]  # Phase 2: Credit card only
        }

        # Add provider-specific configuration
        if strategy.provider == PaymentProvider.STRIPE:
            config["stripe"] = {
                "publishable_key": strategy.get_public_key()
            }
        elif strategy.provider == PaymentProvider.TAPPAY:
            config["tappay"] = strategy.get_app_config()

        return config

    def get_available_providers(self) -> list[PaymentProvider]:
        """
        Get list of available payment providers

        Returns:
            List of configured payment providers
        """
        return list(self.strategies.keys())

    def is_provider_available(self, provider: PaymentProvider) -> bool:
        """
        Check if a payment provider is available

        Args:
            provider: Payment provider to check

        Returns:
            True if provider is configured and available
        """
        return provider in self.strategies