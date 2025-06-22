"""
Telegram API client for sending messages.
"""

import asyncio
import logging
import requests
from typing import Dict, Any

from .config import BotConfig
from .exceptions import TelegramAPIError, MessageDeliveryError

logger = logging.getLogger(__name__)


class TelegramClient:
    """Handles Telegram API interactions."""

    def __init__(self, config: BotConfig):
        """Initialize Telegram client."""
        self.config = config
        self.base_url = f"https://api.telegram.org/bot{config.bot_token}"

    async def send_message(
        self, message: str, parse_mode: str = "Markdown", disable_web_page_preview: bool = True
    ) -> bool:
        """
        Send a message to the configured chat with retry logic.

        Args:
            message: The message text to send
            parse_mode: Message parsing mode (Markdown, HTML, or None)
            disable_web_page_preview: Whether to disable link previews

        Returns:
            bool: True if message was sent successfully

        Raises:
            MessageDeliveryError: If message delivery fails after all retries
        """
        url = f"{self.base_url}/sendMessage"

        payload = {
            "chat_id": self.config.chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }

        for attempt in range(self.config.max_retries):
            try:
                response = requests.post(url, json=payload, timeout=self.config.request_timeout)
                response.raise_for_status()

                result = response.json()
                if result.get("ok"):
                    logger.info(f"Message sent successfully on attempt {attempt + 1}")
                    return True
                else:
                    error_msg = result.get("description", "Unknown error")
                    raise TelegramAPIError(f"Telegram API error: {error_msg}")

            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    delay = 2**attempt  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    raise MessageDeliveryError(
                        f"Failed to send message after {self.config.max_retries} attempts"
                    ) from e

            except TelegramAPIError:
                # Don't retry on API errors (usually permanent)
                raise

        return False

    async def get_me(self) -> Dict[str, Any]:
        """
        Get information about the bot.

        Returns:
            Dict containing bot information

        Raises:
            TelegramAPIError: If the API call fails
        """
        url = f"{self.base_url}/getMe"

        try:
            response = requests.get(url, timeout=self.config.request_timeout)
            response.raise_for_status()

            result = response.json()
            if result.get("ok"):
                return result["result"]
            else:
                error_msg = result.get("description", "Unknown error")
                raise TelegramAPIError(f"Failed to get bot info: {error_msg}")

        except requests.exceptions.RequestException as e:
            raise TelegramAPIError(f"Network error getting bot info: {e}") from e

    async def validate_connection(self) -> bool:
        """
        Validate that the bot can connect to Telegram API.

        Returns:
            bool: True if connection is valid
        """
        try:
            bot_info = await self.get_me()
            logger.info(f"Bot connection validated: @{bot_info.get('username')}")
            return True
        except TelegramAPIError as e:
            logger.error(f"Bot connection validation failed: {e}")
            return False
