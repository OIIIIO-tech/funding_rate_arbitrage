#!/usr/bin/env python3
"""
Test script for the opportunity scanner
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.scanners.opportunity_scanner import OpportunityScanner

async def test_scanner():
    """Test the scanner basic functionality."""
    print("🧪 Testing Opportunity Scanner...")
    print("=" * 50)
    
    try:
        # Test scanner initialization
        print("1. Initializing scanner...")
        scanner = OpportunityScanner()
        print("   ✅ Scanner initialized successfully")
        
        # Test configuration
        print("\n2. Testing configuration...")
        print(f"   Min funding rate: {scanner.config['min_funding_rate']}")
        print(f"   Max risk score: {scanner.config['max_risk_score']}")
        print(f"   Min volume: ${scanner.config['min_volume_24h']:,}")
        print("   ✅ Configuration loaded")
        
        # Test database connection
        print("\n3. Testing database connection...")
        session = scanner.Session()
        session.close()
        print("   ✅ Database connection successful")
        
        # Test exchange connection (if credentials available)
        print("\n4. Testing exchange connection...")
        try:
            from config.settings import get_api_credentials
            credentials = get_api_credentials()
            if credentials.get('apiKey'):
                print("   ✅ API credentials found")
                
                # Quick API test
                import ccxt.async_support as ccxt
                async with ccxt.bybit(scanner.exchange_config) as exchange:
                    await exchange.load_markets()
                    print("   ✅ Exchange connection successful")
            else:
                print("   ⚠️  No API credentials - scanner will work but may have limited data")
        except Exception as e:
            print(f"   ⚠️  Exchange connection issue: {e}")
        
        print("\n✅ Scanner test completed successfully!")
        print("\n🚀 Ready to scan for opportunities!")
        
    except Exception as e:
        print(f"\n❌ Scanner test failed: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = asyncio.run(test_scanner())
    if success:
        print("\n💡 Run 'python scanner_dashboard.py --quick' for a quick scan")
        print("💡 Run 'python scanner_dashboard.py' for continuous monitoring")
    else:
        print("\n💡 Please check the error above and ensure all dependencies are installed")
