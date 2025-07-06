#!/usr/bin/env python3
"""
Simple script to test Bybit API connectivity.
This version doesn't use dotenv - you need to set environment variables manually.
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import ccxt.async_support as ccxt

async def test_api_connection():
    """Test API connection and permissions."""
    print("🔧 Testing Bybit API Connection...")
    print("=" * 50)
    
    # Get credentials from environment variables
    api_key = os.getenv('BYBIT_API_KEY', 'your_api_key_here')
    api_secret = os.getenv('BYBIT_API_SECRET', 'your_api_secret_here')
    testnet = os.getenv('BYBIT_TESTNET', 'false').lower() == 'true'
    
    if api_key == 'your_api_key_here':
        print("❌ API Key not configured!")
        print("Please set BYBIT_API_KEY environment variable")
        print("Or run: export BYBIT_API_KEY='your_actual_key'")
        return False
    
    if api_secret == 'your_api_secret_here':
        print("❌ API Secret not configured!")
        print("Please set BYBIT_API_SECRET environment variable")
        print("Or run: export BYBIT_API_SECRET='your_actual_secret'")
        return False
    
    print(f"✅ API Key: {api_key[:8]}***")
    print(f"✅ Testnet: {testnet}")
    print()
    
    # Initialize exchange
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'testnet': testnet,
            'enableRateLimit': True,
        })
        
        print("🔗 Testing API Connection...")
        
        # Test: Get server time
        try:
            server_time = await exchange.fetch_time()
            print(f"✅ Server Time: Connected")
        except Exception as e:
            print(f"❌ Server Time Error: {e}")
            await exchange.close()
            return False
        
        # Test: Get markets
        try:
            await exchange.load_markets()
            print("✅ Markets: Loaded successfully")
        except Exception as e:
            print(f"❌ Markets Error: {e}")
            await exchange.close()
            return False
        
        # Test spot and futures data
        trading_pairs = {
            'BTC/USDT': 'BTC/USDT:USDT',
            'ETH/USDT': 'ETH/USDT:USDT',
            'SOL/USDT': 'SOL/USDT:USDT'
        }
        
        print("\n📊 Testing Market Data Access...")
        for spot_symbol, perp_symbol in trading_pairs.items():
            try:
                # Test spot ticker
                exchange.options['defaultType'] = 'spot'
                spot_ticker = await exchange.fetch_ticker(spot_symbol)
                print(f"✅ {spot_symbol} (spot): ${spot_ticker['last']:.2f}")
                
                # Test perpetual ticker
                exchange.options['defaultType'] = 'future'
                perp_ticker = await exchange.fetch_ticker(perp_symbol)
                print(f"✅ {perp_symbol} (perp): ${perp_ticker['last']:.2f}")
                
                # Test funding rate
                try:
                    funding_info = await exchange.fetch_funding_rate(perp_symbol)
                    if funding_info and 'fundingRate' in funding_info:
                        rate = funding_info['fundingRate']
                        annual_rate = rate * 365 * 3 * 100 if rate else 0
                        print(f"✅ Funding Rate: {rate:.6f} ({annual_rate:.2f}% annual)")
                    else:
                        print("⚠️  Funding Rate: Available but format unexpected")
                except Exception as e:
                    print(f"⚠️  Funding Rate: {e}")
                
                print()  # Add space between pairs
                
            except Exception as e:
                print(f"❌ {spot_symbol}: {e}")
        
        await exchange.close()
        
        print("=" * 50)
        print("🎉 API Connection Test Complete!")
        print("✅ Your API setup is working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return False

def main():
    """Main function to run the test."""
    print("Bybit API Connection Test (Simplified)")
    print("Make sure you've set your environment variables:")
    print("export BYBIT_API_KEY='your_key'")
    print("export BYBIT_API_SECRET='your_secret'")
    print()
    
    try:
        success = asyncio.run(test_api_connection())
        if success:
            print("\n🚀 Next steps:")
            print("1. Run: python main.py setup")
            print("2. Then: python main.py collect --days 1")
        else:
            print("\n❌ Please fix the issues above and try again")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == '__main__':
    main()
