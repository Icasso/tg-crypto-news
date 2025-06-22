"""
Message builder for constructing bot messages.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from .config import BotConfig
from aave import AaveClient, TokenSymbol

logger = logging.getLogger(__name__)


class MessageComponent(ABC):
    """Abstract base class for message components."""

    @abstractmethod
    async def generate(self) -> Optional[str]:
        """Generate the message component content."""
        pass


class HelloWorldComponent(MessageComponent):
    """Simple hello world message component."""

    def __init__(self, custom_message: Optional[str] = None):
        """Initialize with optional custom message."""
        self.custom_message = custom_message

    async def generate(self) -> Optional[str]:
        """Generate hello world message."""
        if self.custom_message:
            return f"👋 {self.custom_message}"
        return "👋 Hello World! This is your daily message from the Telegram bot!"


class AaveMarketComponent(MessageComponent):
    """AAVE market info message component with table format."""

    def __init__(self, aave_client: AaveClient, target_tokens: list[TokenSymbol] = None):
        """
        Initialize AAVE market component.

        Args:
            aave_client: AAVE client instance
            target_tokens: List of tokens to display (default: ETH, USDC, cbBTC)
        """
        self.aave_client = aave_client
        self.target_tokens = target_tokens or [TokenSymbol.ETH, TokenSymbol.USDC, TokenSymbol.CBBTC]

    async def generate(self) -> str:
        """Generate AAVE market info message in table format."""
        try:
            message_parts = []

            # Header
            message_parts.append("🏦 **AAVE Base Market**")
            message_parts.append("")

            # Fetch data for target tokens
            token_data = []
            for token in self.target_tokens:
                try:
                    reserve = await self.aave_client.get_reserve_data(token)
                    token_data.append(
                        {
                            "symbol": token.value,
                            "supply": reserve.supply_apy_percent,
                            "borrow": reserve.borrow_apy_percent,
                            "utilization": reserve.utilization_percent,
                            "liquidity": reserve.liquidity,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {token.value}: {e}")
                    # Add placeholder data for failed tokens
                    token_data.append(
                        {
                            "symbol": token.value,
                            "supply": 0.0,
                            "borrow": 0.0,
                            "utilization": 0.0,
                            "liquidity": 0.0,
                        }
                    )

            if not token_data:
                return "❌ No market data available"

            # Create card-style layout for better Telegram readability
            for data in token_data:
                symbol = data["symbol"]
                supply = f"{data['supply']:.2f}%" if data["supply"] > 0 else "N/A"
                borrow = f"{data['borrow']:.2f}%" if data["borrow"] > 0 else "N/A"
                utilization = f"{data['utilization']:.1f}%" if data["utilization"] > 0 else "N/A"

                # Format liquidity with appropriate units
                if data["liquidity"] > 1000:
                    liquidity = f"{data['liquidity']:,.0f}"
                elif data["liquidity"] > 0:
                    liquidity = f"{data['liquidity']:.2f}"
                else:
                    liquidity = "N/A"

                # Create card for each token
                message_parts.append(f"💰 **{symbol}**")
                message_parts.append(f"├ 📈 Supply: `{supply}`")
                message_parts.append(f"├ 📉 Borrow: `{borrow}`")
                message_parts.append(f"├ 📊 Utilization: `{utilization}`")
                message_parts.append(f"└ 💧 Liquidity: `{liquidity}`")
                message_parts.append("")

            message_parts.append("")

            # Add AAVE Base markets link
            message_parts.append("🔗 **View Full Markets**")
            message_parts.append(
                "👉 [AAVE Base Markets](https://app.aave.com/?marketName=proto_base_v3)"
            )
            message_parts.append("")

            # Timestamp
            from datetime import datetime

            timestamp = datetime.now().strftime("%H:%M UTC")
            message_parts.append(f"⏰ Updated: {timestamp}")

            return "\n".join(message_parts)

        except Exception as e:
            logger.error(f"Failed to generate AAVE market message: {e}")
            return f"❌ Failed to fetch AAVE market data: {str(e)}"


class MessageBuilder:
    """Builds messages by combining different components."""

    def __init__(self, config: BotConfig):
        """Initialize message builder."""
        self.config = config
        self.components = []

    def add_component(self, component: MessageComponent) -> "MessageBuilder":
        """
        Add a message component.

        Args:
            component: The message component to add

        Returns:
            Self for method chaining
        """
        self.components.append(component)
        return self

    def clear_components(self) -> "MessageBuilder":
        """Clear all components."""
        self.components.clear()
        return self

    async def build(self) -> str:
        """
        Build the complete message from all components.

        Returns:
            The complete message string
        """
        if not self.components:
            # Default to hello world if no components
            default_component = HelloWorldComponent(self.config.message)
            return await default_component.generate() or "Hello World!"

        message_parts = []

        for component in self.components:
            try:
                content = await component.generate()
                if content:
                    message_parts.append(content)
            except Exception as e:
                logger.warning(f"Failed to generate component {component.__class__.__name__}: {e}")
                continue

        if not message_parts:
            logger.warning("No message components generated content, using fallback")
            return "Hello World!"

        # Join parts with double newlines
        return "\n\n".join(message_parts)

    @classmethod
    def create_hello_world_builder(cls, config: BotConfig) -> "MessageBuilder":
        """
        Create a message builder with hello world component.

        Args:
            config: Bot configuration

        Returns:
            MessageBuilder instance with hello world component
        """
        builder = cls(config)
        builder.add_component(HelloWorldComponent(config.message))
        return builder

    def add_aave_market(
        self, aave_client: AaveClient, target_tokens: list[TokenSymbol] = None
    ) -> "MessageBuilder":
        """
        Add AAVE market component.

        Args:
            aave_client: AAVE client instance
            target_tokens: List of tokens to display

        Returns:
            Self for method chaining
        """
        component = AaveMarketComponent(aave_client=aave_client, target_tokens=target_tokens)
        return self.add_component(component)
