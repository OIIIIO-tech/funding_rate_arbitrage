#!/usr/bin/env python3
"""
Funding Rate Arbitrage Scanner Dashboard

A simplified interface to run and monitor the opportunity scanner.
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.scanners.opportunity_scanner import OpportunityScanner

def print_banner():
    """Print the scanner banner."""
    print("=" * 80)
    print("🎯 FUNDING RATE ARBITRAGE OPPORTUNITY SCANNER")
    print("=" * 80)
    print("📊 Real-time monitoring of funding rate arbitrage opportunities")
    print("💰 Tracks spot-futures spreads across BTC, ETH, and SOL on Bybit")
    print("⚡ Identifies profitable long/short funding strategies")
    print("=" * 80)
    print()

def print_help():
    """Print usage help."""
    print("📋 SCANNER COMMANDS:")
    print()
    print("  python scanner_dashboard.py                    # Start live scanning")
    print("  python scanner_dashboard.py --quick            # Quick scan (single pass)")
    print("  python scanner_dashboard.py --aggressive       # Lower thresholds for more opportunities")
    print("  python scanner_dashboard.py --conservative     # Higher thresholds for safer opportunities")
    print("  python scanner_dashboard.py --config           # Show current configuration")
    print()
    print("📊 OPPORTUNITY TYPES:")
    print()
    print("  🟢 LONG_FUNDING: Positive funding rates")
    print("     Strategy: Long spot + Short perpetual (collect funding)")
    print()
    print("  🔴 SHORT_FUNDING: Negative funding rates") 
    print("     Strategy: Short spot + Long perpetual (collect funding)")
    print()
    print("⚡ Press Ctrl+C to stop live scanning")
    print()

async def run_scanner(mode='normal'):
    """Run the scanner with specified mode."""
    scanner = OpportunityScanner()
    
    # Adjust thresholds based on mode
    if mode == 'aggressive':
        print("🔥 AGGRESSIVE MODE - Lower thresholds for more opportunities")
        scanner.config.update({
            'min_funding_rate': 0.00005,  # 0.005% (1.83% annually)
            'max_risk_score': 8,
            'min_volume_24h': 500000,     # $500k minimum
            'max_spread_bps': 15,
        })
    elif mode == 'conservative':
        print("🛡️  CONSERVATIVE MODE - Higher thresholds for safer opportunities")
        scanner.config.update({
            'min_funding_rate': 0.0002,   # 0.02% (7.3% annually)
            'max_risk_score': 5,
            'min_volume_24h': 2000000,    # $2M minimum
            'max_spread_bps': 8,
        })
    
    print(f"⚙️  Configuration:")
    print(f"   Min Funding Rate: {scanner.config['min_funding_rate']:.6f} ({scanner.config['min_funding_rate']*365*3*100:.1f}% annual)")
    print(f"   Max Risk Score: {scanner.config['max_risk_score']}/10")
    print(f"   Min Volume: ${scanner.config['min_volume_24h']:,.0f}")
    print(f"   Max Spread: {scanner.config['max_spread_bps']} bps")
    print(f"   Scan Interval: {scanner.config['scan_interval']} seconds")
    print()
    
    await scanner.start_scanning()

async def quick_scan():
    """Perform a single scan and exit."""
    print("🔍 Performing quick scan...")
    scanner = OpportunityScanner()
    
    try:
        opportunities = await scanner.scan_opportunities()
        await scanner.process_opportunities(opportunities)
        
        if opportunities:
            print(f"\n✅ Found {len(opportunities)} opportunities")
            print("💡 Use 'python scanner_dashboard.py' for continuous monitoring")
        else:
            print("\n📊 No opportunities found at current thresholds")
            print("💡 Try '--aggressive' mode for lower thresholds")
            
    except Exception as e:
        print(f"❌ Error during scan: {e}")

def show_config():
    """Show current scanner configuration."""
    scanner = OpportunityScanner()
    
    print("📋 CURRENT SCANNER CONFIGURATION")
    print("=" * 50)
    print(f"Min Funding Rate: {scanner.config['min_funding_rate']:.6f}")
    print(f"Annual Threshold: {scanner.config['min_funding_rate']*365*3*100:.1f}%")
    print(f"Max Risk Score: {scanner.config['max_risk_score']}/10")
    print(f"Min Daily Volume: ${scanner.config['min_volume_24h']:,.0f}")
    print(f"Max Spread: {scanner.config['max_spread_bps']} basis points")
    print(f"Scan Interval: {scanner.config['scan_interval']} seconds")
    print()
    print("📊 MONITORED PAIRS:")
    for pair in scanner.config.get('pairs', ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']):
        print(f"   • {pair}")
    print()

def main():
    parser = argparse.ArgumentParser(description='Funding Rate Arbitrage Scanner Dashboard')
    parser.add_argument('--quick', action='store_true', 
                       help='Perform single scan and exit')
    parser.add_argument('--aggressive', action='store_true',
                       help='Use aggressive thresholds (more opportunities)')
    parser.add_argument('--conservative', action='store_true',
                       help='Use conservative thresholds (safer opportunities)')
    parser.add_argument('--config', action='store_true',
                       help='Show current configuration')
    parser.add_argument('--help-scanner', action='store_true',
                       help='Show detailed scanner help')
    
    args = parser.parse_args()
    
    # Handle special cases
    if args.help_scanner:
        print_banner()
        print_help()
        return
    
    if args.config:
        print_banner()
        show_config()
        return
    
    # Print banner
    print_banner()
    
    # Check for API credentials
    try:
        from config.settings import get_api_credentials
        credentials = get_api_credentials()
        if not credentials.get('apiKey'):
            print("❌ Error: API credentials not configured")
            print("💡 Please check config/settings.py and ensure API credentials are set")
            return
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return
    
    # Run scanner based on mode
    try:
        if args.quick:
            asyncio.run(quick_scan())
        else:
            mode = 'normal'
            if args.aggressive:
                mode = 'aggressive'
            elif args.conservative:
                mode = 'conservative'
            
            print("🚀 Starting live opportunity scanner...")
            print("⚡ Press Ctrl+C to stop")
            print()
            asyncio.run(run_scanner(mode))
            
    except KeyboardInterrupt:
        print("\n🛑 Scanner stopped by user")
    except Exception as e:
        print(f"\n❌ Scanner error: {e}")
        print("💡 Check logs/opportunity_scanner.log for details")

if __name__ == '__main__':
    main()
