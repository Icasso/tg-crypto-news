"""
Production-ready AAVE client for fetching market data via Web3.
"""

import logging
from typing import Optional, List
import asyncio
from web3 import Web3

from .models import MarketInfo, ReserveData
from .enums import Network, TokenSymbol, ContractType, RateType, NetworkRegistry, AaveConstants
from .exceptions import NetworkError, ContractError, TokenNotFoundError, ConfigurationError
from .utils import RateCalculator, AddressValidator, CacheManager, RetryManager

logger = logging.getLogger(__name__)


class AaveClient:
    """Production-ready AAVE client for fetching market data via Web3."""

    # Minimal Pool ABI for getReserveData
    POOL_ABI = [
        {
            "inputs": [{"name": "asset", "type": "address"}],
            "name": "getReserveData",
            "outputs": [
                {
                    "components": [
                        {"name": "configuration", "type": "uint256"},
                        {"name": "liquidityIndex", "type": "uint128"},
                        {"name": "currentLiquidityRate", "type": "uint128"},
                        {"name": "variableBorrowIndex", "type": "uint128"},
                        {"name": "currentVariableBorrowRate", "type": "uint128"},
                        {"name": "currentStableBorrowRate", "type": "uint128"},
                        {"name": "lastUpdateTimestamp", "type": "uint40"},
                        {"name": "id", "type": "uint16"},
                        {"name": "aTokenAddress", "type": "address"},
                        {"name": "stableDebtTokenAddress", "type": "address"},
                        {"name": "variableDebtTokenAddress", "type": "address"},
                        {"name": "interestRateStrategyAddress", "type": "address"},
                        {"name": "accruedToTreasury", "type": "uint128"},
                        {"name": "unbacked", "type": "uint128"},
                        {"name": "isolationModeTotalDebt", "type": "uint128"},
                    ],
                    "name": "",
                    "type": "tuple",
                }
            ],
            "stateMutability": "view",
            "type": "function",
        }
    ]

    # ERC20 ABI for balance queries
    ERC20_ABI = [
        {
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
    ]

    def __init__(
        self,
        network: Network = Network.BASE,
        enable_cache: bool = True,
        cache_ttl: int = AaveConstants.DEFAULT_CACHE_TTL,
        timeout: int = AaveConstants.DEFAULT_TIMEOUT,
    ):
        """
        Initialize AAVE client.

        Args:
            network: Network to connect to
            enable_cache: Whether to enable caching
            cache_ttl: Cache TTL in seconds
            timeout: Request timeout in seconds
        """
        self.network = network
        self.timeout = timeout

        # Get network configuration
        try:
            self.network_config = NetworkRegistry.get_network_config(network)
        except ValueError as e:
            raise ConfigurationError(f"Unsupported network: {network}") from e

        # Initialize Web3 connection
        try:
            self.w3 = Web3(
                Web3.HTTPProvider(self.network_config.rpc_url, request_kwargs={"timeout": timeout})
            )

            # Validate connection
            if not self.w3.is_connected():
                raise NetworkError(f"Failed to connect to {network.value} network", network.value)

        except Exception as e:
            raise NetworkError(
                f"Failed to initialize Web3 for {network.value}: {str(e)}", network.value
            ) from e

        # Initialize contracts
        try:
            pool_address = self.network_config.get_contract_address(ContractType.POOL)
            self.pool_contract = self.w3.eth.contract(
                address=AddressValidator.validate_address(pool_address, "pool_address"),
                abi=self.POOL_ABI,
            )
        except Exception as e:
            raise ContractError(f"Failed to initialize pool contract: {str(e)}") from e

        # Initialize cache if enabled
        self.cache = CacheManager(cache_ttl) if enable_cache else None

        # Initialize rate calculator
        self.rate_calculator = RateCalculator()

        logger.info(
            f"Initialized AAVE client for {network.value} network "
            f"(v{self.network_config.version.value})"
        )

    def _get_cache_key(self, token: TokenSymbol, operation: str) -> str:
        """Generate cache key."""
        return f"{self.network.value}:{token.value}:{operation}"

    async def _get_reserve_data_raw(self, token: TokenSymbol) -> tuple:
        """
        Get raw reserve data from contract.

        Args:
            token: Token to fetch data for

        Returns:
            Raw reserve data tuple

        Raises:
            TokenNotFoundError: If token not supported
            ContractError: If contract call fails
        """
        try:
            token_address = self.network_config.get_token_address(token)
        except ValueError as e:
            raise TokenNotFoundError(token.value, self.network.value) from e

        try:
            # Get current event loop
            loop = asyncio.get_event_loop()

            # Call contract with retry logic
            async def contract_call():
                return await loop.run_in_executor(
                    None, self.pool_contract.functions.getReserveData(token_address).call
                )

            return await RetryManager.retry_with_backoff(
                contract_call, max_retries=3, base_delay=1.0
            )

        except Exception as e:
            raise ContractError(f"Failed to get reserve data for {token.value}: {str(e)}") from e

    async def _get_liquidity_data(
        self, token: TokenSymbol, a_token_address: str
    ) -> tuple[int, int]:
        """
        Get liquidity data for token.

        Args:
            token: Token symbol
            a_token_address: aToken contract address

        Returns:
            Tuple of (available_liquidity, total_supply)
        """
        try:
            token_address = self.network_config.get_token_address(token)

            # Initialize contracts
            token_contract = self.w3.eth.contract(
                address=AddressValidator.validate_address(token_address), abi=self.ERC20_ABI
            )

            atoken_contract = self.w3.eth.contract(
                address=AddressValidator.validate_address(a_token_address), abi=self.ERC20_ABI
            )

            # Get current event loop
            loop = asyncio.get_event_loop()

            # Fetch data concurrently
            available_liquidity_task = loop.run_in_executor(
                None, token_contract.functions.balanceOf(a_token_address).call
            )

            total_supply_task = loop.run_in_executor(
                None, atoken_contract.functions.totalSupply().call
            )

            available_liquidity, total_supply = await asyncio.gather(
                available_liquidity_task, total_supply_task
            )

            return available_liquidity, total_supply

        except Exception as e:
            logger.warning(f"Failed to get liquidity data for {token.value}: {e}")
            return 0, 0

    async def get_reserve_data(self, token: TokenSymbol) -> ReserveData:
        """
        Get reserve data for a specific token.

        Args:
            token: Token to fetch data for

        Returns:
            ReserveData for the token

        Raises:
            TokenNotFoundError: If token not supported
            ContractError: If contract interaction fails
        """
        # Check cache first
        cache_key = self._get_cache_key(token, "reserve_data")
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached data for {token.value}")
                return cached_data

        try:
            logger.debug(f"Fetching reserve data for {token.value}")

            # Get raw reserve data
            reserve_data = await self._get_reserve_data_raw(token)

            # Parse reserve data tuple
            (
                configuration,
                liquidity_index,
                current_liquidity_rate,
                variable_borrow_index,
                current_variable_borrow_rate,
                current_stable_borrow_rate,
                last_update_timestamp,
                reserve_id,
                a_token_address,
                stable_debt_token_address,
                variable_debt_token_address,
                interest_rate_strategy_address,
                accrued_to_treasury,
                unbacked,
                isolation_mode_total_debt,
            ) = reserve_data

            # Convert rates using utility
            supply_apy = self.rate_calculator.ray_to_apy(current_liquidity_rate, RateType.SUPPLY)
            borrow_apy = self.rate_calculator.ray_to_apy(
                current_variable_borrow_rate, RateType.VARIABLE_BORROW
            )

            # Get liquidity data
            available_liquidity, total_supply = await self._get_liquidity_data(
                token, a_token_address
            )

            # Calculate metrics using utilities
            liquidity = self.rate_calculator.wei_to_token(available_liquidity)
            utilization = self.rate_calculator.calculate_utilization(
                total_supply, available_liquidity
            )

            # Create reserve data
            reserve = ReserveData(
                symbol=token.value,
                supply_rate=supply_apy,
                borrow_rate=borrow_apy,
                liquidity=liquidity,
                utilization=utilization,
            )

            # Cache result
            if self.cache:
                self.cache.set(cache_key, reserve)

            logger.debug(
                f"✅ {token.value}: Supply {supply_apy:.4f} APY, Borrow {borrow_apy:.4f} APY"
            )
            return reserve

        except (TokenNotFoundError, ContractError):
            raise
        except Exception as e:
            raise ContractError(
                f"Failed to process reserve data for {token.value}: {str(e)}"
            ) from e

    async def get_market_info(self, tokens: Optional[List[TokenSymbol]] = None) -> MarketInfo:
        """
        Get market information for specified tokens or all supported tokens.

        Args:
            tokens: List of tokens to fetch (default: all supported tokens)

        Returns:
            MarketInfo with reserve data
        """
        if tokens is None:
            tokens = NetworkRegistry.get_supported_tokens(self.network)

        if not tokens:
            raise ConfigurationError(f"No tokens specified for {self.network.value}")

        logger.info(f"Fetching market data for {len(tokens)} tokens on {self.network.value}")

        reserves = []
        failed_tokens = []

        # Fetch data for each token
        for token in tokens:
            try:
                reserve = await self.get_reserve_data(token)
                reserves.append(reserve)
            except Exception as e:
                logger.warning(f"Failed to fetch data for {token.value}: {e}")
                failed_tokens.append(token.value)
                continue

        if not reserves:
            raise ContractError("No reserve data could be fetched for any token")

        if failed_tokens:
            logger.warning(f"Failed to fetch data for tokens: {', '.join(failed_tokens)}")

        market_info = MarketInfo(network=self.network.value, reserves=reserves)
        logger.info(
            f"Successfully fetched data for {len(reserves)} reserves on {self.network.value}"
        )

        return market_info

    async def get_eth_info(self) -> ReserveData:
        """Get ETH reserve information directly."""
        return await self.get_reserve_data(TokenSymbol.ETH)

    def get_supported_tokens(self) -> List[TokenSymbol]:
        """Get list of supported tokens for current network."""
        return NetworkRegistry.get_supported_tokens(self.network)

    def clear_cache(self) -> None:
        """Clear all cached data."""
        if self.cache:
            self.cache.clear()
            logger.info("Cache cleared")

    async def health_check(self) -> bool:
        """
        Perform health check on the client.

        Returns:
            True if client is healthy
        """
        try:
            # Check Web3 connection
            if not self.w3.is_connected():
                logger.error("Web3 connection failed")
                return False

            # Try to fetch ETH data
            await self.get_eth_info()
            logger.info("Health check passed")
            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
