import argparse
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.data_collectors.data_collector import collect_data
from app.data_collectors.historical_collector import HistoricalDataCollector
from config.settings import DATABASE_PATH
from app.models.funding_rate_models import Base
from sqlalchemy import create_engine

def setup_database():
    """Initialize the database and create all tables."""
    print("Setting up database...")
    engine = create_engine(DATABASE_PATH)
    Base.metadata.create_all(engine)
    print("Database setup completed successfully.")

def main():
    parser = argparse.ArgumentParser(description='Funding Rate Arbitrage System')
    parser.add_argument('action', choices=[
        'setup', 'collect', 'backtest', 'analyze', 'view'
    ], help='Action to perform')
    
    # Data collection arguments
    parser.add_argument('--days', type=int, default=180, 
                       help='Number of days of historical data to collect (default: 180 for 6 months)')
    parser.add_argument('--live', action='store_true', 
                       help='Start live data collection')
    parser.add_argument('--historical', action='store_true',
                       help='Collect comprehensive historical data (6 months by default)')
    
    # Backtesting arguments
    parser.add_argument('--strategy', type=str, default='funding_rate',
                       help='Strategy to backtest (default: funding_rate)')
    parser.add_argument('--start', type=str, 
                       help='Start date for backtest (YYYY-MM-DD)')
    parser.add_argument('--end', type=str,
                       help='End date for backtest (YYYY-MM-DD)')
    parser.add_argument('--capital', type=float, default=100000,
                       help='Initial capital for backtest (default: 100000)')
    parser.add_argument('--max-position', type=float, default=0.1,
                       help='Maximum position size as fraction of capital (default: 0.1)')
    
    # Analysis arguments
    parser.add_argument('--period', type=str, default='1m',
                       help='Analysis period (1w, 1m, 3m, 6m, 1y) (default: 1m)')
    
    # View arguments
    parser.add_argument('--data', type=str, choices=['ohlcv', 'funding_rates', 'opportunities'],
                       help='Type of data to view')
    parser.add_argument('--pair', type=str, 
                       help='Trading pair to view (e.g., BTC/USDT)')

    args = parser.parse_args()

    if args.action == 'setup':
        setup_database()
        
    elif args.action == 'collect':
        if args.live:
            print("Starting live data collection...")
            print("Press Ctrl+C to stop")
            try:
                asyncio.run(continuous_collection())
            except KeyboardInterrupt:
                print("\nData collection stopped.")
        elif args.historical:
            print(f"Starting comprehensive historical data collection for {args.days} days...")
            print("This may take several hours depending on the amount of data.")
            print("Progress will be logged to logs/historical_collection.log")
            try:
                asyncio.run(collect_comprehensive_historical_data(args.days))
                print("\n✅ Historical data collection completed successfully!")
            except KeyboardInterrupt:
                print("\n⚠️  Data collection interrupted by user")
            except Exception as e:
                print(f"\n❌ Error during historical collection: {e}")
        else:
            print(f"Collecting {args.days} days of basic historical data...")
            asyncio.run(collect_historical_data(args.days))
            print("Historical data collection completed.")
            
    elif args.action == 'backtest':
        print(f"Running {args.strategy} backtest...")
        run_backtest(args)
        
    elif args.action == 'analyze':
        print(f"Generating analysis for {args.period} period...")
        generate_analysis(args)
        
    elif args.action == 'view':
        if not args.data or not args.pair:
            print("Error: --data and --pair arguments are required for view action")
            return
        view_data(args.data, args.pair)

async def collect_historical_data(days):
    """Collect historical data for specified number of days."""
    print(f"Basic historical data collection for {days} days...")
    # TODO: Implement basic historical data collection logic
    await collect_data()

async def collect_comprehensive_historical_data(days):
    """Collect comprehensive historical data using the enhanced collector."""
    collector = HistoricalDataCollector()
    await collector.collect_historical_data(days_back=days)

async def continuous_collection():
    """Continuously collect live data."""
    while True:
        try:
            await collect_data()
            print(f"Data collection cycle completed at {datetime.now()}")
            # Wait for next collection cycle (e.g., every minute)
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Error in data collection: {e}")
            await asyncio.sleep(60)  # Wait before retrying

def run_backtest(args):
    """Run backtesting with specified parameters."""
    print("Backtesting functionality would be implemented here.")
    print(f"Strategy: {args.strategy}")
    print(f"Capital: ${args.capital:,.0f}")
    print(f"Max Position: {args.max_position:.1%}")
    if args.start:
        print(f"Start Date: {args.start}")
    if args.end:
        print(f"End Date: {args.end}")
    # TODO: Implement backtesting logic

def generate_analysis(args):
    """Generate performance analysis."""
    print("Analysis functionality would be implemented here.")
    print(f"Period: {args.period}")
    # TODO: Implement analysis logic

def view_data(data_type, pair):
    """View stored data."""
    print(f"Viewing {data_type} data for {pair}...")
    # TODO: Implement data viewing logic

if __name__ == '__main__':
    main()
