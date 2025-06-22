"""Tests for bot.core module."""

import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml

from bot.config import AaveConfig, BotConfig
from bot.core import DailyTelegramBot
from bot.exceptions import ConfigurationError, MessageDeliveryError


class TestDailyTelegramBot:
    """Test cases for DailyTelegramBot class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        aave_config = AaveConfig(
            enabled=True,
            target_tokens=["ETH", "USDC"],
            table_format=True,
        )
        return BotConfig(
            message="Test message",
            bot_token="test_token",
            chat_id="123456789",
            max_retries=3,
            request_timeout=30,
            aave=aave_config,
        )

    @pytest.fixture
    def temp_config_file(self, mock_config):
        """Create a temporary config file."""
        config_data = {
            "message": mock_config.message,
            "max_retries": mock_config.max_retries,
            "request_timeout": mock_config.request_timeout,
            "aave": {
                "enabled": mock_config.aave.enabled,
                "target_tokens": mock_config.aave.target_tokens,
                "table_format": mock_config.aave.table_format,
            },
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name
        
        # Set environment variables
        os.environ["TELEGRAM_BOT_TOKEN"] = mock_config.bot_token
        os.environ["TELEGRAM_CHAT_ID"] = mock_config.chat_id
        
        yield temp_file
        
        # Cleanup
        os.unlink(temp_file)
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        os.environ.pop("TELEGRAM_CHAT_ID", None)

    @pytest.mark.asyncio
    async def test_initialize_success(self, temp_config_file):
        """Test successful bot initialization."""
        bot = DailyTelegramBot(config_path=temp_config_file)
        
        with patch("bot.telegram_client.TelegramClient.validate_connection", new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = True
            
            await bot.initialize()
            
            # Should not raise any exceptions
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_telegram_failure(self, temp_config_file):
        """Test bot initialization with Telegram connection failure."""
        bot = DailyTelegramBot(config_path=temp_config_file)
        
        with patch("bot.telegram_client.TelegramClient.validate_connection", new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = False
            
            with pytest.raises(ConfigurationError):
                await bot.initialize()

    @pytest.mark.asyncio
    async def test_send_daily_message_success(self, temp_config_file):
        """Test successful daily message sending."""
        bot = DailyTelegramBot(config_path=temp_config_file)
        
        with patch("bot.message_builder.MessageBuilder.build", new_callable=AsyncMock) as mock_build, \
             patch("bot.telegram_client.TelegramClient.send_message", new_callable=AsyncMock) as mock_send:
            
            mock_build.return_value = "Test message content"
            mock_send.return_value = True
            
            result = await bot.send_daily_message()
            
            assert result is True
            mock_build.assert_called_once()
            mock_send.assert_called_once_with("Test message content")

    @pytest.mark.asyncio
    async def test_send_daily_message_empty_message(self, temp_config_file):
        """Test daily message sending with empty message."""
        bot = DailyTelegramBot(config_path=temp_config_file)
        
        with patch("bot.message_builder.MessageBuilder.build", new_callable=AsyncMock) as mock_build, \
             patch("bot.telegram_client.TelegramClient.send_message", new_callable=AsyncMock) as mock_send:
            
            mock_build.return_value = ""
            mock_send.return_value = True
            
            result = await bot.send_daily_message()
            
            # Should send "Hello World!" as fallback
            assert result is True
            mock_send.assert_called_once_with("Hello World!")

    @pytest.mark.asyncio
    async def test_send_daily_message_failure(self, temp_config_file):
        """Test daily message sending failure."""
        bot = DailyTelegramBot(config_path=temp_config_file)
        
        with patch("bot.message_builder.MessageBuilder.build", new_callable=AsyncMock) as mock_build, \
             patch("bot.telegram_client.TelegramClient.send_message", new_callable=AsyncMock) as mock_send:
            
            mock_build.return_value = "Test message content"
            mock_send.return_value = False
            
            with pytest.raises(MessageDeliveryError):
                await bot.send_daily_message()

    @pytest.mark.asyncio
    async def test_run_success(self, temp_config_file):
        """Test successful bot run."""
        bot = DailyTelegramBot(config_path=temp_config_file)
        
        with patch.object(bot, "initialize", new_callable=AsyncMock) as mock_init, \
             patch.object(bot, "send_daily_message", new_callable=AsyncMock) as mock_send:
            
            mock_init.return_value = None
            mock_send.return_value = True
            
            await bot.run()
            
            mock_init.assert_called_once()
            mock_send.assert_called_once()

    def test_run_sync_success(self, temp_config_file):
        """Test successful synchronous bot run."""
        bot = DailyTelegramBot(config_path=temp_config_file)
        
        with patch.object(bot, "run", new_callable=AsyncMock) as mock_async_run, \
             patch("asyncio.run") as mock_asyncio_run:
            
            mock_async_run.return_value = None
            mock_asyncio_run.return_value = None
            
            bot.run_sync()
            
            mock_async_run.assert_called_once()
            mock_asyncio_run.assert_called_once()

    def test_run_sync_configuration_error(self, temp_config_file):
        """Test synchronous run with configuration error."""
        bot = DailyTelegramBot(config_path=temp_config_file)
        
        with patch.object(bot, "run", new_callable=AsyncMock) as mock_run, \
             patch("asyncio.run") as mock_asyncio_run, \
             patch("sys.exit") as mock_exit:
            
            mock_asyncio_run.side_effect = ConfigurationError("Config error")
            
            bot.run_sync()
            
            mock_exit.assert_called_once_with(2) 