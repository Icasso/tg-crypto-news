#!/usr/bin/env python3
"""
Comprehensive demo of production-ready AAVE client features.
"""

import asyncio
import logging
import sys
import os
from decimal import Decimal

# Add parent directory to path to import aave module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aave import (
    AaveClient, Network, TokenSymbol, 
    NetworkError, ContractError, TokenNotFoundError,
    RateCalculator, AddressValidator, AaveConstants
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_functionality():
    """Demo basic AAVE client functionality."""
    print("\n" + "="*60)
    print("🚀 BASIC FUNCTIONALITY DEMO")
    print("="*60)
    
    try:
        # Initialize client with configuration
        client = AaveClient(
            network=Network.BASE,
            enable_cache=True,
            cache_ttl=300,  # 5 minutes
            timeout=30
        )
        
        print(f"✅ Initialized AAVE client for {Network.BASE.value}")
        print(f"📋 Supported tokens: {[token.value for token in client.get_supported_tokens()]}")
        
        # Health check
        is_healthy = await client.health_check()
        print(f"🏥 Health check: {'✅ PASSED' if is_healthy else '❌ FAILED'}")
        
        return client
        
    except Exception as e:
        print(f"❌ Basic functionality failed: {e}")
        raise


async def demo_token_data_fetching(client: AaveClient):
    """Demo fetching data for different tokens."""
    print("\n" + "="*60)
    print("💰 TOKEN DATA FETCHING DEMO")
    print("="*60)
    
    # Test individual token fetching
    for token in [TokenSymbol.ETH, TokenSymbol.USDC]:
        try:
            print(f"\n📊 Fetching {token.value} data...")
            reserve = await client.get_reserve_data(token)
            
            print(f"  Supply APY: {reserve.supply_apy_percent:.2f}%")
            print(f"  Borrow APY: {reserve.borrow_apy_percent:.2f}%")
            print(f"  Utilization: {reserve.utilization_percent:.1f}%")
            print(f"  Liquidity: {reserve.liquidity:,.0f} {token.value}")
            print(f"  ✅ {token.value} data fetched successfully")
            
        except TokenNotFoundError as e:
            print(f"  ❌ {token.value} not available: {e}")
        except Exception as e:
            print(f"  ❌ Failed to fetch {token.value}: {e}")


async def demo_market_analysis(client: AaveClient):
    """Demo market analysis features."""
    print("\n" + "="*60)
    print("📈 MARKET ANALYSIS DEMO")
    print("="*60)
    
    try:
        # Get all market data
        market_info = await client.get_market_info()
        
        print(f"📊 Market Overview ({market_info.network}):")
        print(f"  Total reserves: {len(market_info.reserves)}")
        
        # Find best supply and borrow rates
        best_supply = max(market_info.reserves, key=lambda r: r.supply_rate)
        best_borrow = min(market_info.reserves, key=lambda r: r.borrow_rate)
        
        print(f"\n🏆 Best Supply Rate:")
        print(f"  {best_supply.symbol}: {best_supply.supply_apy_percent:.2f}% APY")
        
        print(f"\n💸 Lowest Borrow Rate:")
        print(f"  {best_borrow.symbol}: {best_borrow.borrow_apy_percent:.2f}% APY")
        
        # Market statistics
        avg_supply = sum(r.supply_rate for r in market_info.reserves) / len(market_info.reserves)
        avg_borrow = sum(r.borrow_rate for r in market_info.reserves) / len(market_info.reserves)
        
        print(f"\n📊 Market Statistics:")
        print(f"  Average Supply APY: {RateCalculator.apy_to_percentage(avg_supply):.2f}%")
        print(f"  Average Borrow APY: {RateCalculator.apy_to_percentage(avg_borrow):.2f}%")
        
        # High utilization tokens
        high_util_tokens = [r for r in market_info.reserves if r.utilization > Decimal('0.8')]
        if high_util_tokens:
            print(f"\n⚠️  High Utilization Tokens (>80%):")
            for reserve in high_util_tokens:
                print(f"  {reserve.symbol}: {reserve.utilization_percent:.1f}%")
        
    except Exception as e:
        print(f"❌ Market analysis failed: {e}")


async def demo_error_handling():
    """Demo comprehensive error handling."""
    print("\n" + "="*60)
    print("🛡️  ERROR HANDLING DEMO")
    print("="*60)
    
    # Test invalid network (this would fail in real scenario)
    print("🧪 Testing error scenarios...")
    
    try:
        # Test with invalid token (simulated)
        client = AaveClient(network=Network.BASE)
        
        # This should work
        await client.get_reserve_data(TokenSymbol.ETH)
        print("✅ Valid token request succeeded")
        
        # Test network connectivity
        is_connected = client.w3.is_connected()
        print(f"🌐 Network connectivity: {'✅ Connected' if is_connected else '❌ Disconnected'}")
        
    except NetworkError as e:
        print(f"🌐 Network Error: {e}")
    except ContractError as e:
        print(f"📄 Contract Error: {e}")
    except TokenNotFoundError as e:
        print(f"💰 Token Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


async def demo_utility_functions():
    """Demo utility functions."""
    print("\n" + "="*60)
    print("🔧 UTILITY FUNCTIONS DEMO")
    print("="*60)
    
    # Rate calculations
    print("📊 Rate Calculator Demo:")
    
    # Example ray values (AAVE format)
    supply_ray = 17742678435827338000000000  # ~1.77% APY
    borrow_ray = 25037895988736530000000000  # ~2.50% APY
    
    supply_apy = RateCalculator.ray_to_apy(supply_ray)
    borrow_apy = RateCalculator.ray_to_apy(borrow_ray)
    
    print(f"  Ray {supply_ray} → {RateCalculator.apy_to_percentage(supply_apy):.2f}% Supply APY")
    print(f"  Ray {borrow_ray} → {RateCalculator.apy_to_percentage(borrow_apy):.2f}% Borrow APY")
    
    # Wei conversions
    print("\n💰 Wei Converter Demo:")
    wei_amount = 15000000000000000000000  # 15,000 ETH in wei
    token_amount = RateCalculator.wei_to_token(wei_amount)
    print(f"  {wei_amount} wei → {token_amount:,.0f} ETH")
    
    # Address validation
    print("\n📍 Address Validator Demo:")
    test_addresses = [
        "0xa238dd80c259a72e81d7e4664a9801593f98d1c5",  # Pool address
        "0x4200000000000000000000000000000000000006",  # WETH address
    ]
    
    for addr in test_addresses:
        try:
            checksum_addr = AddressValidator.validate_address(addr)
            print(f"  {addr[:10]}... → {checksum_addr[:10]}... ✅")
        except Exception as e:
            print(f"  {addr[:10]}... → ❌ {e}")
    
    # Constants
    print(f"\n⚙️  AAVE Constants:")
    print(f"  RAY precision: {AaveConstants.RAY:,}")
    print(f"  Token decimals: {AaveConstants.TOKEN_DECIMALS}")
    print(f"  Max APY: {AaveConstants.MAX_APY * 100}%")
    print(f"  Cache TTL: {AaveConstants.DEFAULT_CACHE_TTL}s")


async def demo_caching_performance(client: AaveClient):
    """Demo caching performance benefits."""
    print("\n" + "="*60)
    print("💾 CACHING PERFORMANCE DEMO")
    print("="*60)
    
    import time
    
    # Clear cache first
    client.clear_cache()
    
    # First call (no cache)
    print("🔄 First call (contract fetch)...")
    start_time = time.time()
    await client.get_reserve_data(TokenSymbol.ETH)
    first_call_time = time.time() - start_time
    
    # Second call (cached)
    print("⚡ Second call (cached)...")
    start_time = time.time()
    await client.get_reserve_data(TokenSymbol.ETH)
    second_call_time = time.time() - start_time
    
    # Performance comparison
    speedup = first_call_time / second_call_time if second_call_time > 0 else float('inf')
    
    print(f"\n📊 Performance Results:")
    print(f"  Contract call: {first_call_time:.3f}s")
    print(f"  Cached call: {second_call_time:.3f}s")
    print(f"  Speedup: {speedup:.1f}x faster")
    print(f"  Time saved: {(first_call_time - second_call_time) * 1000:.1f}ms")
    
    # Multiple token performance test
    print(f"\n🚀 Batch Performance Test:")
    tokens = [TokenSymbol.ETH, TokenSymbol.USDC]
    
    client.clear_cache()
    start_time = time.time()
    for token in tokens:
        try:
            await client.get_reserve_data(token)
        except:
            pass
    batch_time = time.time() - start_time
    
    print(f"  Fetched {len(tokens)} tokens in {batch_time:.3f}s")
    print(f"  Average per token: {batch_time/len(tokens):.3f}s")


async def demo_network_comparison():
    """Demo multi-network comparison capabilities."""
    print("\n" + "="*60)
    print("🌐 NETWORK COMPARISON DEMO")
    print("="*60)
    
    networks_to_test = [Network.BASE, Network.ETHEREUM]
    results = {}
    
    for network in networks_to_test:
        try:
            print(f"\n📡 Testing {network.value}...")
            client = AaveClient(network=network, timeout=10)
            
            # Test connectivity
            if not await client.health_check():
                print(f"  ❌ {network.value} health check failed")
                continue
            
            # Get supported tokens
            supported_tokens = client.get_supported_tokens()
            print(f"  📋 Supported tokens: {[t.value for t in supported_tokens]}")
            
            # Try to get ETH data if available
            if TokenSymbol.ETH in supported_tokens:
                try:
                    eth_data = await client.get_reserve_data(TokenSymbol.ETH)
                    results[network.value] = {
                        'supply_apy': eth_data.supply_apy_percent,
                        'borrow_apy': eth_data.borrow_apy_percent,
                        'utilization': eth_data.utilization_percent
                    }
                    print(f"  ✅ ETH rates: Supply {eth_data.supply_apy_percent:.2f}%, Borrow {eth_data.borrow_apy_percent:.2f}%")
                except Exception as e:
                    print(f"  ❌ Failed to get ETH data: {e}")
            
        except Exception as e:
            print(f"  ❌ {network.value} failed: {e}")
    
    # Compare results
    if len(results) > 1:
        print(f"\n🔍 Cross-Network ETH Comparison:")
        for network, data in results.items():
            print(f"  {network}: Supply {data['supply_apy']:.2f}%, Borrow {data['borrow_apy']:.2f}%")


async def main():
    """Run comprehensive AAVE client demo."""
    print("🚀 PRODUCTION-READY AAVE CLIENT DEMO")
    print("="*80)
    
    try:
        # Basic functionality
        client = await demo_basic_functionality()
        
        # Token data fetching
        await demo_token_data_fetching(client)
        
        # Market analysis
        await demo_market_analysis(client)
        
        # Caching performance
        await demo_caching_performance(client)
        
        # Utility functions
        await demo_utility_functions()
        
        # Error handling
        await demo_error_handling()
        
        # Network comparison (optional - may be slow)
        # await demo_network_comparison()
        
        print("\n" + "="*80)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.exception("Demo error")


if __name__ == "__main__":
    asyncio.run(main()) 