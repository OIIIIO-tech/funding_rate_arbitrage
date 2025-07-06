#!/usr/bin/env python3
"""
Debug script to see current market data and funding rates
"""

import asyncio
import ccxt.async_support as ccxt
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.settings import TRADING_PAIRS, get_api_credentials

async def debug_market_data():
    """Debug current market data and funding rates."""
    print("🔍 DEBUGGING CURRENT MARKET DATA")
    print("=" * 60)
    
    credentials = get_api_credentials()
    exchange_config = {
        'apiKey': credentials['apiKey'],
        'secret': credentials['secret'],
        'testnet': credentials['testnet'],
        'enableRateLimit': True,
    }
    
    async with ccxt.bybit(exchange_config) as exchange:
        await exchange.load_markets()
        
        for pair_name, pair_info in TRADING_PAIRS.items():
            print(f"\n💰 {pair_name}")
            print("-" * 40)
            
            try:
                # Get spot data
                exchange.options['defaultType'] = 'spot'
                spot_ticker = await exchange.fetch_ticker(pair_info['spot'])
                
                # Get futures data
                exchange.options['defaultType'] = 'future'
                futures_ticker = await exchange.fetch_ticker(pair_info['perpetual'])
                funding_rate_info = await exchange.fetch_funding_rate(pair_info['perpetual'])
                
                # Calculate metrics
                spot_price = float(spot_ticker['last'])
                futures_price = float(futures_ticker['last'])
                funding_rate = float(funding_rate_info['fundingRate'])
                
                # Calculate basis and annualized rate
                basis = futures_price - spot_price
                basis_bps = (basis / spot_price) * 10000
                annual_funding_rate = funding_rate * 365 * 3 * 100
                
                # Get volume
                volume_24h = futures_ticker.get('quoteVolume', 0)
                
                print(f"📈 Spot Price: ${spot_price:,.2f}")
                print(f"🔮 Futures Price: ${futures_price:,.2f}")
                print(f"💸 Funding Rate: {funding_rate:.6f} ({annual_funding_rate:+.2f}% annual)")
                print(f"📊 Basis: {basis_bps:+.1f} bps")
                print(f"📈 24h Volume: ${volume_24h:,.0f}")
                print(f"⏰ Next Funding: {funding_rate_info.get('fundingDatetime', 'Unknown')}")
                
                # Show if this would be an opportunity
                min_funding_rate = 0.00005  # Aggressive threshold
                if abs(funding_rate) >= min_funding_rate:
                    if funding_rate > 0:
                        print(f"🟢 OPPORTUNITY: Long spot, short perpetual")
                    else:
                        print(f"🔴 OPPORTUNITY: Short spot, long perpetual")
                else:
                    print(f"⚪ No opportunity (funding rate too low)")
                
            except Exception as e:
                print(f"❌ Error getting data for {pair_name}: {e}")
    
    print(f"\n⚙️  THRESHOLDS:")
    print(f"   Min Funding Rate: 0.00005 (1.83% annual)")
    print(f"   Min Volume: $500,000")
    print(f"   Max Spread: 15 bps")

if __name__ == '__main__':
    asyncio.run(debug_market_data())
