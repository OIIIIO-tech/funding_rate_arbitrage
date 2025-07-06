#!/usr/bin/env python3
"""
Script to check what historical data we have in the database.
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.models.funding_rate_models import Base, PerpetualOHLCV, SpotOHLCV, FundingRate
from config.settings import DATABASE_PATH

def check_database():
    """Check what data we have in the database."""
    print("🔍 Checking Historical Data in Database")
    print("="*60)
    
    # Create database connection
    engine = create_engine(DATABASE_PATH)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if tables exist
        tables = ['spot_ohlcv', 'perpetual_ohlcv', 'funding_rates']
        
        for table in tables:
            try:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"✅ {table.upper()}: {count:,} records")
            except Exception as e:
                print(f"❌ {table.upper()}: Table not found or error - {e}")
        
        print("\n" + "="*60)
        print("📊 DETAILED BREAKDOWN BY TRADING PAIR")
        print("="*60)
        
        # Check each trading pair
        pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        
        for pair in pairs:
            print(f"\n💰 {pair}:")
            print("-" * 40)
            
            # Spot data
            try:
                spot_count = session.query(SpotOHLCV).filter_by(symbol=pair).count()
                if spot_count > 0:
                    earliest_spot = session.query(SpotOHLCV.timestamp).filter_by(symbol=pair).order_by(SpotOHLCV.timestamp.asc()).first()
                    latest_spot = session.query(SpotOHLCV.timestamp).filter_by(symbol=pair).order_by(SpotOHLCV.timestamp.desc()).first()
                    print(f"  📈 Spot OHLCV: {spot_count:,} records")
                    print(f"     From: {earliest_spot[0].strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"     To:   {latest_spot[0].strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print(f"  📈 Spot OHLCV: No data")
            except Exception as e:
                print(f"  📈 Spot OHLCV: Error - {e}")
            
            # Perpetual data
            try:
                perp_count = session.query(PerpetualOHLCV).filter_by(symbol=pair).count()
                if perp_count > 0:
                    earliest_perp = session.query(PerpetualOHLCV.timestamp).filter_by(symbol=pair).order_by(PerpetualOHLCV.timestamp.asc()).first()
                    latest_perp = session.query(PerpetualOHLCV.timestamp).filter_by(symbol=pair).order_by(PerpetualOHLCV.timestamp.desc()).first()
                    print(f"  🔮 Perpetual OHLCV: {perp_count:,} records")
                    print(f"     From: {earliest_perp[0].strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"     To:   {latest_perp[0].strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print(f"  🔮 Perpetual OHLCV: No data")
            except Exception as e:
                print(f"  🔮 Perpetual OHLCV: Error - {e}")
            
            # Funding rate data
            try:
                funding_count = session.query(FundingRate).filter_by(symbol=pair).count()
                if funding_count > 0:
                    earliest_funding = session.query(FundingRate.timestamp).filter_by(symbol=pair).order_by(FundingRate.timestamp.asc()).first()
                    latest_funding = session.query(FundingRate.timestamp).filter_by(symbol=pair).order_by(FundingRate.timestamp.desc()).first()
                    print(f"  💸 Funding Rates: {funding_count:,} records")
                    print(f"     From: {earliest_funding[0].strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"     To:   {latest_funding[0].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Show some recent funding rates
                    recent_rates = session.query(FundingRate).filter_by(symbol=pair).order_by(FundingRate.timestamp.desc()).limit(3).all()
                    if recent_rates:
                        print(f"     Recent rates:")
                        for rate in recent_rates:
                            annual_rate = rate.funding_rate * 365 * 3 * 100 if rate.funding_rate else 0
                            print(f"       {rate.timestamp.strftime('%Y-%m-%d %H:%M')}: {rate.funding_rate:.6f} ({annual_rate:+.2f}% annual)")
                else:
                    print(f"  💸 Funding Rates: No data")
            except Exception as e:
                print(f"  💸 Funding Rates: Error - {e}")
        
        print("\n" + "="*60)
        print("📈 SAMPLE DATA PREVIEW")
        print("="*60)
        
        # Show sample recent data
        try:
            # Recent spot data
            recent_spot = session.query(SpotOHLCV).order_by(SpotOHLCV.timestamp.desc()).first()
            if recent_spot:
                print(f"\n📊 Most Recent Spot Data:")
                print(f"   Symbol: {recent_spot.symbol}")
                print(f"   Time: {recent_spot.timestamp}")
                print(f"   Price: ${recent_spot.close:,.2f}")
                print(f"   Volume: {recent_spot.volume:,.2f}")
            
            # Recent perpetual data
            recent_perp = session.query(PerpetualOHLCV).order_by(PerpetualOHLCV.timestamp.desc()).first()
            if recent_perp:
                print(f"\n🔮 Most Recent Perpetual Data:")
                print(f"   Symbol: {recent_perp.symbol}")
                print(f"   Time: {recent_perp.timestamp}")
                print(f"   Price: ${recent_perp.close:,.2f}")
                print(f"   Volume: {recent_perp.volume:,.2f}")
                if recent_perp.mark_price:
                    print(f"   Mark Price: ${recent_perp.mark_price:,.2f}")
            
            # Recent funding rate
            recent_funding = session.query(FundingRate).order_by(FundingRate.timestamp.desc()).first()
            if recent_funding:
                annual_rate = recent_funding.funding_rate * 365 * 3 * 100 if recent_funding.funding_rate else 0
                print(f"\n💸 Most Recent Funding Rate:")
                print(f"   Symbol: {recent_funding.symbol}")
                print(f"   Time: {recent_funding.timestamp}")
                print(f"   Rate: {recent_funding.funding_rate:.6f} ({annual_rate:+.2f}% annual)")
                if recent_funding.perpetual_price and recent_funding.spot_price:
                    basis = ((recent_funding.perpetual_price - recent_funding.spot_price) / recent_funding.spot_price) * 100
                    print(f"   Basis: {basis:+.4f}%")
        
        except Exception as e:
            print(f"Error showing sample data: {e}")
        
        print("\n" + "="*60)
        print("✅ Database Inspection Complete!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
    finally:
        session.close()

def check_database_file():
    """Check if database file exists and its size."""
    print("📁 DATABASE FILE INFORMATION")
    print("="*60)
    
    # Extract database file path from DATABASE_PATH
    if DATABASE_PATH.startswith('sqlite:///'):
        db_file_path = DATABASE_PATH[10:]  # Remove 'sqlite:///' prefix
        
        if os.path.exists(db_file_path):
            file_size = os.path.getsize(db_file_path)
            size_mb = file_size / (1024 * 1024)
            print(f"✅ Database file exists: {db_file_path}")
            print(f"📊 File size: {file_size:,} bytes ({size_mb:.2f} MB)")
            
            # Check last modified time
            mod_time = datetime.fromtimestamp(os.path.getmtime(db_file_path))
            print(f"⏰ Last modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"❌ Database file not found: {db_file_path}")
    else:
        print(f"⚠️  Non-SQLite database: {DATABASE_PATH}")

if __name__ == '__main__':
    print("🔍 FUNDING RATE ARBITRAGE - DATABASE INSPECTION")
    print("="*60)
    print(f"⏰ Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check database file first
    check_database_file()
    print()
    
    # Check database contents
    check_database()
