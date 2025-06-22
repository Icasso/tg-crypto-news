"""
Production-ready AAVE integration package for fetching market data via Web3.
"""

from .aave_client import AaveClient
from .models import MarketInfo, ReserveData
from .enums import Network, TokenSymbol, ContractType, RateType, AaveConstants
from .exceptions import (
    AaveError,
    NetworkError,
    ContractError,
    TokenNotFoundError,
    ConfigurationError,
    RateCalculationError,
    TimeoutError,
    ValidationError,
)
from .utils import RateCalculator, AddressValidator, CacheManager, RetryManager

__version__ = "1.0.0"

__all__ = [
    # Core classes
    "AaveClient",
    "MarketInfo",
    "ReserveData",
    # Enums
    "Network",
    "TokenSymbol",
    "ContractType",
    "RateType",
    "AaveConstants",
    # Exceptions
    "AaveError",
    "NetworkError",
    "ContractError",
    "TokenNotFoundError",
    "ConfigurationError",
    "RateCalculationError",
    "TimeoutError",
    "ValidationError",
    # Utilities
    "RateCalculator",
    "AddressValidator",
    "CacheManager",
    "RetryManager",
]
