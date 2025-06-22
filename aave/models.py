"""
Simple data models for AAVE market information.
"""

from dataclasses import dataclass
from typing import List
from decimal import Decimal


@dataclass
class ReserveData:
    """AAVE reserve data for a specific asset."""

    symbol: str
    supply_rate: Decimal  # APY as decimal (e.g., 0.05 for 5%)
    borrow_rate: Decimal  # APY as decimal
    liquidity: Decimal  # Total available liquidity
    utilization: Decimal  # Utilization rate as decimal

    @property
    def supply_apy_percent(self) -> float:
        """Get supply APY as percentage."""
        return float(self.supply_rate * 100)

    @property
    def borrow_apy_percent(self) -> float:
        """Get borrow APY as percentage."""
        return float(self.borrow_rate * 100)

    @property
    def utilization_percent(self) -> float:
        """Get utilization as percentage."""
        return float(self.utilization * 100)


@dataclass
class MarketInfo:
    """AAVE market information containing all reserves."""

    network: str
    reserves: List[ReserveData]

    def get_reserve(self, symbol: str) -> ReserveData:
        """Get reserve data by symbol."""
        for reserve in self.reserves:
            if reserve.symbol.upper() == symbol.upper():
                return reserve
        raise ValueError(f"Reserve {symbol} not found")

    def get_top_supply_rates(self, limit: int = 5) -> List[ReserveData]:
        """Get reserves with highest supply rates."""
        return sorted(self.reserves, key=lambda r: r.supply_rate, reverse=True)[:limit]
