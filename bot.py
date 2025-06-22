#!/usr/bin/env python3
"""
Daily Telegram Bot - Entry Point
Production-ready Telegram bot with modular architecture.
"""

import sys
import logging

# Load environment variables from .env file for local testing
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv not installed, skip (fine for production)
    pass

# Import the main bot class
from bot.core import DailyTelegramBot

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    """Main entry point."""
    try:
        # Create and run the bot
        bot = DailyTelegramBot()
        bot.run_sync()
    except Exception as e:
        logging.error(f"Failed to start bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
