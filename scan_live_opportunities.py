#!/usr/bin/env python3
"""
Live opportunity scanner with ultra-aggressive settings to capture current opportunities
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.scanners.opportunity_scanner import OpportunityScanner

async def scan_live_opportunities():
    """Scan with ultra-aggressive settings to find current opportunities."""
    print("🔥 LIVE OPPORTUNITY SCANNER - ULTRA AGGRESSIVE MODE")
    print("=" * 70)
    
    scanner = OpportunityScanner()
    
    # Ultra-aggressive settings
    scanner.config.update({
        'min_funding_rate': 0.00003,    # 0.003% (1.1% annually)
        'max_risk_score': 10,           # Accept all risk levels
        'min_volume_24h': 100000,       # $100k minimum
        'max_spread_bps': 50,           # Very wide spreads accepted
    })
    
    print(f"⚙️  ULTRA-AGGRESSIVE CONFIGURATION:")
    print(f"   Min Funding Rate: {scanner.config['min_funding_rate']:.6f} ({scanner.config['min_funding_rate']*365*3*100:.1f}% annual)")
    print(f"   Max Risk Score: {scanner.config['max_risk_score']}/10")
    print(f"   Min Volume: ${scanner.config['min_volume_24h']:,.0f}")
    print(f"   Max Spread: {scanner.config['max_spread_bps']} bps")
    print()
    
    try:
        opportunities = await scanner.scan_opportunities()
        await scanner.process_opportunities(opportunities)
        
        if opportunities:
            print(f"\n🎯 SUCCESS: Found {len(opportunities)} live opportunities!")
            print("\n💡 NEXT STEPS:")
            print("1. Analyze each opportunity carefully")
            print("2. Consider your risk tolerance")
            print("3. Check funding times (next funding at 16:00 UTC)")
            print("4. Monitor for changes in funding rates")
        else:
            print("\n⚠️  No opportunities found even with ultra-aggressive settings")
            print("💡 Market conditions may be unfavorable right now")
            
    except Exception as e:
        print(f"❌ Error during scan: {e}")

if __name__ == '__main__':
    asyncio.run(scan_live_opportunities())
