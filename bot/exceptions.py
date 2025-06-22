"""
Custom exceptions for the Telegram bot.
"""


class BotError(Exception):
    """Base exception for bot-related errors."""

    pass


class ConfigurationError(BotError):
    """Raised when there's a configuration error."""

    pass


class TelegramAPIError(BotError):
    """Raised when Telegram API calls fail."""

    pass


class MessageDeliveryError(BotError):
    """Raised when message delivery fails after all retries."""

    pass


class ExternalAPIError(BotError):
    """Raised when external API calls fail."""

    pass
