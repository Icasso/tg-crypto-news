"""
Tests for bot core functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from bot.core import DailyTelegramBot
from bot.exceptions import ConfigurationError, MessageDeliveryError


class TestDailyTelegramBot:
    """Test cases for DailyTelegramBot."""

    @pytest.fixture
    def mock_config(self):
        """Mock bot configuration."""
        config = Mock()
        config.bot_token = "test_token"
        config.chat_id = "test_chat_id"
        config.aave.enabled = True
        config.aave.target_tokens = ["ETH", "USDC"]
        return config

    @pytest.fixture
    def bot(self):
        """Create bot instance."""
        return DailyTelegramBot("test_config.yaml")

    def test_bot_initialization(self, bot):
        """Test bot initializes with correct config path."""
        assert bot.config_path == "test_config.yaml"
        assert bot._config_manager is None
        assert bot._telegram_client is None

    @pytest.mark.asyncio
    async def test_initialize_success(self, bot, mock_config):
        """Test successful bot initialization."""
        with patch.object(bot, "config", mock_config):
            with patch.object(bot, "telegram_client") as mock_client:
                mock_client.validate_connection = AsyncMock(return_value=True)
                
                await bot.initialize()
                
                mock_client.validate_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_telegram_failure(self, bot, mock_config):
        """Test initialization failure due to Telegram connection."""
        with patch.object(bot, "config", mock_config):
            with patch.object(bot, "telegram_client") as mock_client:
                mock_client.validate_connection = AsyncMock(return_value=False)
                
                with pytest.raises(ConfigurationError):
                    await bot.initialize()

    @pytest.mark.asyncio
    async def test_send_daily_message_success(self, bot):
        """Test successful message sending."""
        with patch.object(bot, "message_builder") as mock_builder:
            with patch.object(bot, "telegram_client") as mock_client:
                mock_builder.build = AsyncMock(return_value="Test message")
                mock_client.send_message = AsyncMock(return_value=True)
                
                result = await bot.send_daily_message()
                
                assert result is True
                mock_builder.build.assert_called_once()
                mock_client.send_message.assert_called_once_with("Test message")

    @pytest.mark.asyncio
    async def test_send_daily_message_empty_message(self, bot):
        """Test handling of empty message."""
        with patch.object(bot, "message_builder") as mock_builder:
            with patch.object(bot, "telegram_client") as mock_client:
                mock_builder.build = AsyncMock(return_value="")
                mock_client.send_message = AsyncMock(return_value=True)
                
                result = await bot.send_daily_message()
                
                assert result is True
                mock_client.send_message.assert_called_once_with("Hello World!")

    @pytest.mark.asyncio
    async def test_send_daily_message_failure(self, bot):
        """Test message sending failure."""
        with patch.object(bot, "message_builder") as mock_builder:
            with patch.object(bot, "telegram_client") as mock_client:
                mock_builder.build = AsyncMock(return_value="Test message")
                mock_client.send_message = AsyncMock(return_value=False)
                
                with pytest.raises(MessageDeliveryError):
                    await bot.send_daily_message()

    @pytest.mark.asyncio
    async def test_run_success(self, bot):
        """Test successful bot run."""
        with patch.object(bot, "initialize", new_callable=AsyncMock) as mock_init:
            with patch.object(bot, "send_daily_message", new_callable=AsyncMock) as mock_send:
                mock_send.return_value = True
                
                await bot.run()
                
                mock_init.assert_called_once()
                mock_send.assert_called_once()

    def test_run_sync_success(self, bot):
        """Test successful synchronous run."""
        with patch.object(bot, "run", new_callable=AsyncMock) as mock_run:
            with patch("asyncio.run") as mock_asyncio_run:
                bot.run_sync()
                
                mock_asyncio_run.assert_called_once_with(mock_run.return_value)

    def test_run_sync_configuration_error(self, bot):
        """Test synchronous run with configuration error."""
        with patch.object(bot, "run", new_callable=AsyncMock) as mock_run:
            with patch("asyncio.run") as mock_asyncio_run:
                with patch("sys.exit") as mock_exit:
                    mock_asyncio_run.side_effect = ConfigurationError("Config error")
                    
                    bot.run_sync()
                    
                    mock_exit.assert_called_once_with(2) 