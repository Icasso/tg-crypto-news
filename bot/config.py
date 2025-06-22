"""
Configuration management for the Telegram bot.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AaveConfig:
    """AAVE service configuration."""

    enabled: bool = True
    target_tokens: list[str] = None
    table_format: bool = True

    def __post_init__(self):
        """Initialize default target tokens if not provided."""
        if self.target_tokens is None:
            self.target_tokens = ["ETH", "USDC", "cbBTC"]


@dataclass
class BotConfig:
    """Bot configuration data class."""

    bot_token: str
    chat_id: str
    weather_api_key: Optional[str] = None
    message: str = "Hello World!"
    max_retries: int = 3
    request_timeout: int = 15
    aave: Optional[AaveConfig] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID is required")

        # Initialize AAVE config if not provided
        if self.aave is None:
            self.aave = AaveConfig()


class ConfigManager:
    """Manages bot configuration from environment variables and YAML files."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration manager."""
        self.config_path = config_path
        self._config: Optional[BotConfig] = None

    def load_config(self) -> BotConfig:
        """Load and validate configuration."""
        if self._config is not None:
            return self._config

        # Load from YAML file
        yaml_config = self._load_yaml_config()

        # Load from environment variables
        env_config = self._load_env_config()

        # Merge configurations (env takes precedence)
        merged_config = {**yaml_config, **env_config}

        # Handle AAVE config separately
        aave_config = None
        if "aave" in merged_config:
            aave_data = merged_config.pop("aave")
            if isinstance(aave_data, dict):
                aave_config = AaveConfig(**aave_data)

        # Create and validate config object
        self._config = BotConfig(**merged_config, aave=aave_config)

        logger.info("Configuration loaded successfully")
        return self._config

    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file) or {}

            logger.info(f"YAML configuration loaded from {self.config_path}")
            return config

        except FileNotFoundError:
            logger.warning(f"Configuration file {self.config_path} not found")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            raise

    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}

        # Required environment variables
        if bot_token := os.getenv("TELEGRAM_BOT_TOKEN"):
            config["bot_token"] = bot_token

        if chat_id := os.getenv("TELEGRAM_CHAT_ID"):
            config["chat_id"] = chat_id

        # Optional environment variables
        if weather_api_key := os.getenv("WEATHER_API_KEY"):
            config["weather_api_key"] = weather_api_key

        if max_retries := os.getenv("MAX_RETRIES"):
            try:
                config["max_retries"] = int(max_retries)
            except ValueError:
                logger.warning(f"Invalid MAX_RETRIES value: {max_retries}")

        if timeout := os.getenv("REQUEST_TIMEOUT"):
            try:
                config["request_timeout"] = int(timeout)
            except ValueError:
                logger.warning(f"Invalid REQUEST_TIMEOUT value: {timeout}")

        logger.info("Environment configuration loaded")
        return config

    @property
    def config(self) -> BotConfig:
        """Get the current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config
