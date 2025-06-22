"""
Enums for AAVE integration configuration.
"""

from enum import Enum, IntEnum
from typing import Dict


class Network(Enum):
    """Supported blockchain networks."""

    BASE = "base"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    AVALANCHE = "avalanche"


class TokenSymbol(Enum):
    """Supported token symbols."""

    ETH = "ETH"
    WETH = "WETH"
    USDC = "USDC"
    USDT = "USDT"
    DAI = "DAI"
    WBTC = "WBTC"
    CBBTC = "cbBTC"
    LINK = "LINK"
    UNI = "UNI"
    AAVE = "AAVE"


class ContractType(Enum):
    """AAVE contract types."""

    POOL = "pool"
    POOL_DATA_PROVIDER = "pool_data_provider"
    PRICE_ORACLE = "price_oracle"
    ACL_MANAGER = "acl_manager"


class RateType(Enum):
    """Interest rate types."""

    SUPPLY = "supply"
    VARIABLE_BORROW = "variable_borrow"
    STABLE_BORROW = "stable_borrow"


class AaveVersion(Enum):
    """AAVE protocol versions."""

    V2 = "v2"
    V3 = "v3"


class NetworkConfig:
    """Network configuration container."""

    def __init__(
        self,
        network: Network,
        version: AaveVersion,
        rpc_url: str,
        contracts: Dict[ContractType, str],
        tokens: Dict[TokenSymbol, str],
        chain_id: int,
    ):
        self.network = network
        self.version = version
        self.rpc_url = rpc_url
        self.contracts = contracts
        self.tokens = tokens
        self.chain_id = chain_id

    def get_contract_address(self, contract_type: ContractType) -> str:
        """Get contract address by type."""
        if contract_type not in self.contracts:
            raise ValueError(f"Contract {contract_type} not available for {self.network}")
        return self.contracts[contract_type]

    def get_token_address(self, token: TokenSymbol) -> str:
        """Get token address by symbol."""
        if token not in self.tokens:
            raise ValueError(f"Token {token} not available for {self.network}")
        return self.tokens[token]


class NetworkRegistry:
    """Registry of supported networks and their configurations."""

    NETWORKS: Dict[Network, NetworkConfig] = {
        Network.BASE: NetworkConfig(
            network=Network.BASE,
            version=AaveVersion.V3,
            rpc_url="https://base.llamarpc.com",
            contracts={
                ContractType.POOL: "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
                ContractType.POOL_DATA_PROVIDER: "0xd82a47fdebB5bf5329b09441C3DaB4b5df2153Ad",
            },
            tokens={
                TokenSymbol.ETH: "0x4200000000000000000000000000000000000006",  # WETH on Base
                TokenSymbol.USDC: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
                TokenSymbol.CBBTC: "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",  # cbBTC on Base
                TokenSymbol.DAI: "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",  # DAI on Base
            },
            chain_id=8453,
        ),
        Network.ETHEREUM: NetworkConfig(
            network=Network.ETHEREUM,
            version=AaveVersion.V3,
            rpc_url="https://eth.llamarpc.com",
            contracts={
                ContractType.POOL: "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
                ContractType.POOL_DATA_PROVIDER: "0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3",
            },
            tokens={
                TokenSymbol.ETH: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                TokenSymbol.USDC: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                TokenSymbol.USDT: "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                TokenSymbol.DAI: "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            },
            chain_id=1,
        ),
    }

    @classmethod
    def get_network_config(cls, network: Network) -> NetworkConfig:
        """Get network configuration."""
        if network not in cls.NETWORKS:
            raise ValueError(f"Network {network} not supported")
        return cls.NETWORKS[network]

    @classmethod
    def get_supported_networks(cls) -> list[Network]:
        """Get list of supported networks."""
        return list(cls.NETWORKS.keys())

    @classmethod
    def get_supported_tokens(cls, network: Network) -> list[TokenSymbol]:
        """Get list of supported tokens for a network."""
        config = cls.get_network_config(network)
        return list(config.tokens.keys())


class AaveConstants:
    """AAVE protocol constants."""

    # Ray precision (10^27)
    RAY = 10**27

    # Decimal precision for most tokens
    TOKEN_DECIMALS = 18

    # Maximum reasonable APY (100%)
    MAX_APY = 1.0

    # Request timeouts
    DEFAULT_TIMEOUT = 30
    RETRY_TIMEOUT = 10

    # Cache settings
    DEFAULT_CACHE_TTL = 300  # 5 minutes

    # Rate calculation constants
    SECONDS_PER_YEAR = 365 * 24 * 3600


class ErrorCodes(IntEnum):
    """Error codes for AAVE operations."""

    SUCCESS = 0
    NETWORK_ERROR = 1001
    CONTRACT_ERROR = 1002
    TOKEN_NOT_FOUND = 1003
    INVALID_CONFIGURATION = 1004
    RATE_CALCULATION_ERROR = 1005
    TIMEOUT_ERROR = 1006
    VALIDATION_ERROR = 1007
