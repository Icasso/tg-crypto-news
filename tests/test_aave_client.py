"""
Tests for AAVE client functionality.
"""

import pytest
from unittest.mock import Mock, patch
from aave import AaveClient, Network, TokenSymbol, NetworkError, TokenNotFoundError


class TestAaveClient:
    """Test cases for AaveClient."""

    @pytest.fixture
    def mock_web3(self):
        """Mock Web3 instance."""
        with patch("aave.aave_client.Web3") as mock_web3:
            mock_instance = Mock()
            mock_instance.is_connected.return_value = True
            mock_web3.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def aave_client(self, mock_web3):
        """Create AaveClient instance with mocked Web3."""
        return AaveClient(network=Network.BASE)

    def test_client_initialization(self, aave_client):
        """Test client initializes correctly."""
        assert aave_client.network == Network.BASE
        assert aave_client.network_config is not None

    def test_invalid_network_raises_error(self):
        """Test that invalid network raises ConfigurationError."""
        with patch("aave.aave_client.NetworkRegistry.get_network_config") as mock_registry:
            mock_registry.side_effect = ValueError("Unsupported network")
            
            with pytest.raises(Exception):  # ConfigurationError
                AaveClient(network=Network.BASE)

    @pytest.mark.asyncio
    async def test_get_reserve_data_success(self, aave_client):
        """Test successful reserve data retrieval."""
        # Mock contract call response
        mock_reserve_data = (
            0,  # configuration
            10**27,  # liquidityIndex
            50000000000000000000000000,  # currentLiquidityRate (5% in ray)
            10**27,  # variableBorrowIndex
            75000000000000000000000000,  # currentVariableBorrowRate (7.5% in ray)
            0,  # currentStableBorrowRate
            1640995200,  # lastUpdateTimestamp
            1,  # id
            "0x1234567890123456789012345678901234567890",  # aTokenAddress
            "0x1234567890123456789012345678901234567890",  # stableDebtTokenAddress
            "0x1234567890123456789012345678901234567890",  # variableDebtTokenAddress
            "0x1234567890123456789012345678901234567890",  # interestRateStrategyAddress
            0,  # accruedToTreasury
            0,  # unbacked
            0,  # isolationModeTotalDebt
        )
        
        with patch.object(aave_client, "_get_reserve_data_raw", return_value=mock_reserve_data):
            with patch.object(aave_client, "_get_liquidity_data", return_value=(1000, 2000)):
                reserve_data = await aave_client.get_reserve_data(TokenSymbol.ETH)
                
                assert reserve_data.symbol == "ETH"
                assert reserve_data.supply_apy_percent > 0
                assert reserve_data.borrow_apy_percent > 0

    @pytest.mark.asyncio
    async def test_get_reserve_data_token_not_found(self, aave_client):
        """Test token not found error."""
        with patch.object(aave_client.network_config, "get_token_address") as mock_get_token:
            mock_get_token.side_effect = ValueError("Token not found")
            
            with pytest.raises(TokenNotFoundError):
                await aave_client.get_reserve_data(TokenSymbol.ETH)

    @pytest.mark.asyncio
    async def test_health_check_success(self, aave_client):
        """Test successful health check."""
        with patch.object(aave_client.w3.eth, "get_block_number", return_value=12345):
            result = await aave_client.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, aave_client):
        """Test failed health check."""
        with patch.object(aave_client.w3.eth, "get_block_number", side_effect=Exception("Network error")):
            result = await aave_client.health_check()
            assert result is False

    def test_get_supported_tokens(self, aave_client):
        """Test getting supported tokens."""
        tokens = aave_client.get_supported_tokens()
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(token, TokenSymbol) for token in tokens)

    def test_cache_functionality(self, aave_client):
        """Test cache operations."""
        # Test cache key generation
        cache_key = aave_client._get_cache_key(TokenSymbol.ETH, "test")
        assert "ETH" in cache_key
        assert "test" in cache_key
        
        # Test cache clear
        aave_client.clear_cache()
        # Should not raise any errors 