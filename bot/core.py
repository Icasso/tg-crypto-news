"""
Core bot class that orchestrates all components.
"""

import logging
import sys
from typing import Optional

from .config import ConfigManager, BotConfig
from .telegram_client import TelegramClient
from .message_builder import MessageBuilder
from .exceptions import BotError, ConfigurationError, MessageDeliveryError
from aave import AaveClient, Network, TokenSymbol

logger = logging.getLogger(__name__)


class DailyTelegramBot:
    """Main bot class that orchestrates all components."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the bot.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self._config_manager: Optional[ConfigManager] = None
        self._telegram_client: Optional[TelegramClient] = None
        self._message_builder: Optional[MessageBuilder] = None
        self._aave_client: Optional[AaveClient] = None

    @property
    def config_manager(self) -> ConfigManager:
        """Get the configuration manager (lazy initialization)."""
        if self._config_manager is None:
            self._config_manager = ConfigManager(self.config_path)
        return self._config_manager

    @property
    def config(self) -> BotConfig:
        """Get the bot configuration."""
        return self.config_manager.config

    @property
    def telegram_client(self) -> TelegramClient:
        """Get the Telegram client (lazy initialization)."""
        if self._telegram_client is None:
            self._telegram_client = TelegramClient(self.config)
        return self._telegram_client

    @property
    def message_builder(self) -> MessageBuilder:
        """Get the message builder (lazy initialization)."""
        if self._message_builder is None:
            self._message_builder = self._create_message_builder()
        return self._message_builder

    def _create_message_builder(self) -> MessageBuilder:
        """Create the appropriate message builder based on configuration."""
        builder = MessageBuilder(self.config)

        # Add AAVE component if enabled
        if self.config.aave.enabled:
            # Convert string symbols to TokenSymbol enums
            target_tokens = []
            for token_str in self.config.aave.target_tokens:
                try:
                    target_tokens.append(TokenSymbol(token_str))
                except ValueError:
                    logger.warning(f"Invalid token symbol: {token_str}, skipping")

            if not target_tokens:
                logger.warning("No valid target tokens found, using default ETH")
                target_tokens = [TokenSymbol.ETH]

            builder.add_aave_market(aave_client=self.aave_client, target_tokens=target_tokens)
        # If AAVE is not enabled, MessageBuilder will use default hello world

        return builder

    @property
    def aave_client(self) -> AaveClient:
        """Get the AAVE client (lazy initialization)."""
        if self._aave_client is None:
            # Use base network for ETH data
            self._aave_client = AaveClient(network=Network.BASE)
        return self._aave_client

    async def initialize(self) -> None:
        """Initialize and validate all bot components."""
        try:
            logger.info("Initializing bot...")

            # Load and validate configuration
            config = self.config
            logger.info(f"Configuration loaded for chat ID: {config.chat_id}")

            # Validate Telegram connection
            if not await self.telegram_client.validate_connection():
                raise ConfigurationError("Failed to validate Telegram connection")

            logger.info("Bot initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise ConfigurationError(f"Bot initialization failed: {e}") from e

    async def send_daily_message(self) -> bool:
        """
        Send the daily message.

        Returns:
            bool: True if message was sent successfully

        Raises:
            MessageDeliveryError: If message delivery fails
        """
        try:
            logger.info("Building daily message...")

            # Build the message
            message = await self.message_builder.build()

            if not message.strip():
                logger.warning("Generated message is empty")
                message = "Hello World!"

            logger.info(f"Sending message: {message[:100]}...")

            # Send the message
            success = await self.telegram_client.send_message(message)

            if success:
                logger.info("Daily message sent successfully")
                return True
            else:
                raise MessageDeliveryError("Failed to send daily message")

        except Exception as e:
            logger.error(f"Failed to send daily message: {e}")
            raise

    async def run(self) -> None:
        """
        Main execution method.

        Raises:
            BotError: If any bot operation fails
        """
        try:
            # Initialize bot components
            await self.initialize()

            # Send daily message
            await self.send_daily_message()

            logger.info("Bot execution completed successfully")

        except BotError:
            # Re-raise bot errors as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error during bot execution: {e}")
            raise BotError(f"Bot execution failed: {e}") from e

    def run_sync(self) -> None:
        """
        Synchronous wrapper for the main run method.
        Handles exceptions and exits with appropriate codes.
        """
        import asyncio

        try:
            asyncio.run(self.run())
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(2)  # Configuration error
        except MessageDeliveryError as e:
            logger.error(f"Message delivery error: {e}")
            sys.exit(3)  # Delivery error
        except BotError as e:
            logger.error(f"Bot error: {e}")
            sys.exit(1)  # General bot error
        except KeyboardInterrupt:
            logger.info("Bot execution interrupted by user")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)  # General error
