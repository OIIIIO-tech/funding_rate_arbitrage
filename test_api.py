#!/usr/bin/env python3
"""
Simple script to test Bybit API connectivity and credentials.
Run this after setting up your .env file to verify everything works.
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import ccxt.async_support as ccxt
from config.settings import get_api_credentials, TRADING_PAIRS

async def test_api_connection():
    """Test API connection and permissions."""
    print("🔧 Testing Bybit API Connection...")
    print("=" * 50)
    
    # Get credentials
    credentials = get_api_credentials()
    
    if not credentials['apiKey'] or credentials['apiKey'] == 'your_api_key_here':
        print("❌ API Key not configured!")
        print("Please update BYBIT_API_KEY in your .env file")
        return False
    
    if not credentials['secret'] or credentials['secret'] == 'your_api_secret_here':
        print("❌ API Secret not configured!")
        print("Please update BYBIT_API_SECRET in your .env file")
        return False
    
    print(f"✅ API Key: {credentials['apiKey'][:8]}***")
    print(f"✅ Testnet: {credentials['testnet']}")
    print()
    
    # Initialize exchange
    try:
        exchange = ccxt.bybit({
            'apiKey': credentials['apiKey'],
            'secret': credentials['secret'],
            'testnet': credentials['testnet'],
            'enableRateLimit': True,
        })
        
        print("🔗 Testing API Connection...")
        
        # Test 1: Get server time
        try:
            server_time = await exchange.fetch_time()
            print(f"✅ Server Time: {server_time}")
        except Exception as e:
            print(f"❌ Server Time Error: {e}")
            return False
        
        # Test 2: Get account info (if possible)
        try:
            # This might fail with read-only keys, which is fine
            balance = await exchange.fetch_balance()
            print("✅ Account Access: Success")
        except Exception as e:
            if "permission" in str(e).lower() or "auth" in str(e).lower():
                print("✅ Account Access: Read-only (expected for data collection)")
            else:
                print(f"⚠️  Account Access: {e}")
        
        # Test 3: Fetch market data for each trading pair
        print("\n📊 Testing Market Data Access...")
        for pair, info in TRADING_PAIRS.items():
            try:
                # Test spot data
                spot_ticker = await exchange.fetch_ticker(info['spot'])
                print(f"✅ {info['spot']}: ${spot_ticker['last']:.2f}")
                
                # Test perpetual data
                await exchange.load_markets()
                exchange.options['defaultType'] = 'future'
                perp_ticker = await exchange.fetch_ticker(info['perpetual'])
                print(f"✅ {info['perpetual']}: ${perp_ticker['last']:.2f}")
                
                # Test funding rate
                try:
                    funding_rate = await exchange.fetch_funding_rate(info['perpetual'])
                    if funding_rate and 'fundingRate' in funding_rate:
                        rate = funding_rate['fundingRate']
                        annual_rate = rate * 365 * 3 * 100  # Convert to annual %
                        print(f"✅ Funding Rate: {rate:.6f} ({annual_rate:.2f}% annual)")
                    else:
                        print("⚠️  Funding Rate: Data format unexpected")
                except Exception as e:
                    print(f"⚠️  Funding Rate: {e}")
                
            except Exception as e:
                print(f"❌ {pair}: {e}")
        
        await exchange.close()
        
        print("\n" + "=" * 50)
        print("🎉 API Connection Test Complete!")
        print("✅ Your setup is ready for data collection")
        return True
        
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return False

def main():
    """Main function to run the test."""
    print("Bybit API Connection Test")
    print("Make sure you've updated your .env file with real API credentials")
    print()
    
    try:
        success = asyncio.run(test_api_connection())
        if success:
            print("\n🚀 You can now run: python main.py setup")
            print("🚀 Then try: python main.py collect --days 1")
        else:
            print("\n❌ Please fix the issues above and try again")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == '__main__':
    main()
