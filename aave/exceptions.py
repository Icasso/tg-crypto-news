"""
Custom exceptions for AAVE operations.
"""

from .enums import ErrorCodes


class AaveError(Exception):
    """Base exception for AAVE operations."""

    def __init__(self, message: str, error_code: ErrorCodes = ErrorCodes.SUCCESS):
        super().__init__(message)
        self.error_code = error_code
        self.message = message

    def __str__(self) -> str:
        return f"[{self.error_code.name}] {self.message}"


class NetworkError(AaveError):
    """Network-related errors."""

    def __init__(self, message: str, network: str = None):
        super().__init__(message, ErrorCodes.NETWORK_ERROR)
        self.network = network


class ContractError(AaveError):
    """Contract interaction errors."""

    def __init__(self, message: str, contract_address: str = None):
        super().__init__(message, ErrorCodes.CONTRACT_ERROR)
        self.contract_address = contract_address


class TokenNotFoundError(AaveError):
    """Token not found errors."""

    def __init__(self, token_symbol: str, network: str = None):
        message = f"Token {token_symbol} not found"
        if network:
            message += f" on {network}"
        super().__init__(message, ErrorCodes.TOKEN_NOT_FOUND)
        self.token_symbol = token_symbol
        self.network = network


class ConfigurationError(AaveError):
    """Configuration-related errors."""

    def __init__(self, message: str):
        super().__init__(message, ErrorCodes.INVALID_CONFIGURATION)


class RateCalculationError(AaveError):
    """Rate calculation errors."""

    def __init__(self, message: str, raw_rate: int = None):
        super().__init__(message, ErrorCodes.RATE_CALCULATION_ERROR)
        self.raw_rate = raw_rate


class TimeoutError(AaveError):
    """Timeout errors."""

    def __init__(self, message: str, timeout_seconds: int = None):
        super().__init__(message, ErrorCodes.TIMEOUT_ERROR)
        self.timeout_seconds = timeout_seconds


class ValidationError(AaveError):
    """Validation errors."""

    def __init__(self, message: str, field: str = None):
        super().__init__(message, ErrorCodes.VALIDATION_ERROR)
        self.field = field
