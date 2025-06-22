"""
Utility functions for AAVE operations.
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import Optional, Union

from .enums import AaveConstants, RateType
from .exceptions import RateCalculationError, ValidationError

logger = logging.getLogger(__name__)


class RateCalculator:
    """Utility class for AAVE rate calculations."""

    @staticmethod
    def ray_to_apy(ray_rate: Union[int, str], rate_type: RateType = RateType.SUPPLY) -> Decimal:
        """
        Convert AAVE ray rate to APY.

        Args:
            ray_rate: Ray rate value (int or string)
            rate_type: Type of rate for logging purposes

        Returns:
            APY as decimal (e.g., 0.05 for 5%)

        Raises:
            RateCalculationError: If conversion fails
        """
        if not ray_rate or ray_rate == 0:
            return Decimal("0")

        try:
            # Convert to Decimal for precision
            rate_decimal = Decimal(str(ray_rate))
            ray_decimal = Decimal(str(AaveConstants.RAY))

            # Convert ray rate to decimal APY
            apy = rate_decimal / ray_decimal

            # Validate result
            if apy < 0:
                logger.warning(f"Negative APY calculated: {apy} for {rate_type}")
                return Decimal("0")

            # Apply maximum cap
            max_apy = Decimal(str(AaveConstants.MAX_APY))
            if apy > max_apy:
                logger.warning(f"APY {apy} exceeds maximum {max_apy}, capping for {rate_type}")
                apy = max_apy

            return apy

        except (InvalidOperation, ValueError, OverflowError) as e:
            raise RateCalculationError(
                f"Failed to convert ray rate {ray_rate} to APY: {str(e)}",
                raw_rate=int(ray_rate) if isinstance(ray_rate, (int, str)) else None,
            ) from e

    @staticmethod
    def apy_to_percentage(apy: Decimal) -> float:
        """Convert APY decimal to percentage."""
        try:
            return float(apy * 100)
        except (InvalidOperation, OverflowError):
            return 0.0

    @staticmethod
    def wei_to_token(
        wei_amount: Union[int, str], decimals: int = AaveConstants.TOKEN_DECIMALS
    ) -> Decimal:
        """
        Convert wei amount to token amount.

        Args:
            wei_amount: Amount in wei
            decimals: Token decimals (default 18)

        Returns:
            Token amount as Decimal
        """
        try:
            wei_decimal = Decimal(str(wei_amount))
            divisor = Decimal(10**decimals)
            return wei_decimal / divisor
        except (InvalidOperation, ValueError) as e:
            logger.warning(f"Failed to convert wei {wei_amount} to token: {e}")
            return Decimal("0")

    @staticmethod
    def calculate_utilization(
        total_supply: Union[int, str], available_liquidity: Union[int, str]
    ) -> Decimal:
        """
        Calculate utilization rate.

        Args:
            total_supply: Total supply amount
            available_liquidity: Available liquidity amount

        Returns:
            Utilization rate as decimal (0-1)
        """
        try:
            supply_decimal = Decimal(str(total_supply))
            liquidity_decimal = Decimal(str(available_liquidity))

            if supply_decimal <= 0:
                return Decimal("0")

            borrowed = supply_decimal - liquidity_decimal
            if borrowed <= 0:
                return Decimal("0")

            utilization = borrowed / supply_decimal

            # Ensure utilization is between 0 and 1
            return max(Decimal("0"), min(utilization, Decimal("1")))

        except (InvalidOperation, ValueError, ZeroDivisionError) as e:
            logger.warning(f"Failed to calculate utilization: {e}")
            return Decimal("0")


class AddressValidator:
    """Utility class for address validation."""

    @staticmethod
    def is_valid_ethereum_address(address: str) -> bool:
        """
        Validate Ethereum address format.

        Args:
            address: Address to validate

        Returns:
            True if valid format
        """
        if not address or not isinstance(address, str):
            return False

        # Remove 0x prefix if present
        if address.startswith("0x"):
            address = address[2:]

        # Check length (40 hex characters)
        if len(address) != 40:
            return False

        # Check if all characters are valid hex
        try:
            int(address, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_address(address: str, field_name: str = "address") -> str:
        """
        Validate and normalize Ethereum address to checksum format.

        Args:
            address: Address to validate
            field_name: Field name for error messages

        Returns:
            Checksum address with 0x prefix

        Raises:
            ValidationError: If address is invalid
        """
        if not AddressValidator.is_valid_ethereum_address(address):
            raise ValidationError(f"Invalid Ethereum address: {address}", field=field_name)

        # Ensure 0x prefix
        if not address.startswith("0x"):
            address = "0x" + address

        # Convert to checksum address using Web3
        try:
            from web3 import Web3

            return Web3.to_checksum_address(address)
        except Exception as e:
            raise ValidationError(
                f"Failed to convert address to checksum format: {address}", field=field_name
            ) from e


class CacheManager:
    """Simple in-memory cache manager."""

    def __init__(self, default_ttl: int = AaveConstants.DEFAULT_CACHE_TTL):
        self.default_ttl = default_ttl
        self._cache = {}
        self._timestamps = {}

    def get(self, key: str) -> Optional[any]:
        """Get cached value if not expired."""
        import time

        if key not in self._cache:
            return None

        # Check if expired
        if key in self._timestamps:
            if time.time() - self._timestamps[key] > self.default_ttl:
                self.delete(key)
                return None

        return self._cache[key]

    def set(self, key: str, value: any, ttl: Optional[int] = None) -> None:
        """Set cached value with TTL."""
        import time

        self._cache[key] = value
        self._timestamps[key] = time.time()

    def delete(self, key: str) -> None:
        """Delete cached value."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self._timestamps.clear()


class RetryManager:
    """Utility for handling retries with exponential backoff."""

    @staticmethod
    async def retry_with_backoff(
        func, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0
    ):
        """
        Retry function with exponential backoff.

        Args:
            func: Async function to retry
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        import asyncio

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await func()
            except Exception as e:
                last_exception = e

                if attempt == max_retries:
                    break

                # Calculate delay with exponential backoff
                delay = min(base_delay * (2**attempt), max_delay)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)

        raise last_exception
