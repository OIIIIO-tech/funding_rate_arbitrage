import ccxt.async_support as ccxt
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import time
import pandas as pd

from app.models.funding_rate_models import Base, PerpetualOHLCV, SpotOHLCV, FundingRate
from config.settings import (
    DATABASE_PATH, TRADING_PAIRS, get_api_credentials, 
    DATA_COLLECTION, FUNDING_RATE
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/historical_collection.log'),
        logging.StreamHandler()
    ]
)

class HistoricalDataCollector:
    def __init__(self):
        self.engine = create_engine(DATABASE_PATH)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Initialize exchange
        credentials = get_api_credentials()
        self.exchange_config = {
            'apiKey': credentials['apiKey'],
            'secret': credentials['secret'],
            'testnet': credentials['testnet'],
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}  # Will change as needed
        }
        
    async def collect_historical_data(self, days_back=180):
        """
        Collect historical OHLCV and funding rate data for the last N days.
        
        Args:
            days_back (int): Number of days to look back (default: 180 for 6 months)
        """
        logging.info(f"Starting historical data collection for {days_back} days...")
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        logging.info(f"Collection period: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
        
        async with ccxt.bybit(self.exchange_config) as exchange:
            await exchange.load_markets()
            
            for pair_name, pair_info in TRADING_PAIRS.items():
                logging.info(f"Collecting data for {pair_name}...")
                
                # Collect spot data
                await self._collect_spot_data(exchange, pair_name, pair_info['spot'], start_time, end_time)
                
                # Collect perpetual data
                await self._collect_perpetual_data(exchange, pair_name, pair_info['perpetual'], start_time, end_time)
                
                # Collect funding rate data
                await self._collect_funding_rate_data(exchange, pair_name, pair_info['perpetual'], start_time, end_time)
                
                # Add delay between pairs to respect rate limits
                await asyncio.sleep(1)
        
        logging.info("Historical data collection completed!")
    
    async def _collect_spot_data(self, exchange, pair_name, symbol, start_time, end_time):
        """Collect spot OHLCV data."""
        logging.info(f"  Collecting spot data for {symbol}...")
        
        exchange.options['defaultType'] = 'spot'
        
        try:
            # Get existing data to avoid duplicates
            session = self.Session()
            latest_record = session.query(SpotOHLCV.timestamp).filter_by(
                symbol=pair_name
            ).order_by(SpotOHLCV.timestamp.desc()).first()
            
            # Determine start point
            if latest_record:
                collection_start = max(latest_record.timestamp, start_time)
                logging.info(f"    Resuming from: {collection_start}")
            else:
                collection_start = start_time
                logging.info(f"    Starting from: {collection_start}")
            
            session.close()
            
            # Collect data in batches
            current_time = collection_start
            total_records = 0
            
            while current_time < end_time:
                batch_end = min(current_time + timedelta(hours=16), end_time)  # 16 hours per batch
                
                try:
                    since = int(current_time.timestamp() * 1000)
                    limit = min(1000, DATA_COLLECTION['batch_size'])
                    
                    ohlcv_data = await exchange.fetch_ohlcv(
                        symbol, 
                        DATA_COLLECTION['interval'], 
                        since=since, 
                        limit=limit
                    )
                    
                    if not ohlcv_data:
                        logging.warning(f"    No data returned for {symbol} at {current_time}")
                        break
                    
                    # Store data
                    records_added = self._store_spot_data(pair_name, ohlcv_data)
                    total_records += records_added
                    
                    # Update progress
                    progress = ((current_time - collection_start) / (end_time - collection_start)) * 100
                    logging.info(f"    Progress: {progress:.1f}% - Added {records_added} records")
                    
                    # Move to next batch
                    if len(ohlcv_data) < limit:
                        break  # No more data available
                    
                    current_time = datetime.fromtimestamp(ohlcv_data[-1][0] / 1000) + timedelta(minutes=1)
                    
                    # Rate limiting
                    await asyncio.sleep(DATA_COLLECTION['rate_limit_delay'])
                    
                except Exception as e:
                    logging.error(f"    Error collecting spot data batch: {e}")
                    current_time += timedelta(hours=1)  # Skip ahead
                    await asyncio.sleep(2)
            
            logging.info(f"  Spot data collection complete: {total_records} total records")
            
        except Exception as e:
            logging.error(f"  Failed to collect spot data for {symbol}: {e}")
    
    async def _collect_perpetual_data(self, exchange, pair_name, symbol, start_time, end_time):
        """Collect perpetual OHLCV data with mark and index prices."""
        logging.info(f"  Collecting perpetual data for {symbol}...")
        
        exchange.options['defaultType'] = 'future'
        
        try:
            # Get existing data to avoid duplicates
            session = self.Session()
            latest_record = session.query(PerpetualOHLCV.timestamp).filter_by(
                symbol=pair_name
            ).order_by(PerpetualOHLCV.timestamp.desc()).first()
            
            # Determine start point
            if latest_record:
                collection_start = max(latest_record.timestamp, start_time)
                logging.info(f"    Resuming from: {collection_start}")
            else:
                collection_start = start_time
                logging.info(f"    Starting from: {collection_start}")
            
            session.close()
            
            # Collect data in batches
            current_time = collection_start
            total_records = 0
            
            while current_time < end_time:
                try:
                    since = int(current_time.timestamp() * 1000)
                    limit = min(1000, DATA_COLLECTION['batch_size'])
                    
                    ohlcv_data = await exchange.fetch_ohlcv(
                        symbol, 
                        DATA_COLLECTION['interval'], 
                        since=since, 
                        limit=limit
                    )
                    
                    if not ohlcv_data:
                        logging.warning(f"    No perpetual data returned for {symbol} at {current_time}")
                        break
                    
                    # Try to get mark price data (may not be available for historical)
                    mark_prices = await self._get_mark_prices(exchange, symbol, ohlcv_data)
                    
                    # Store data
                    records_added = self._store_perpetual_data(pair_name, ohlcv_data, mark_prices)
                    total_records += records_added
                    
                    # Update progress
                    progress = ((current_time - collection_start) / (end_time - collection_start)) * 100
                    logging.info(f"    Progress: {progress:.1f}% - Added {records_added} records")
                    
                    # Move to next batch
                    if len(ohlcv_data) < limit:
                        break
                    
                    current_time = datetime.fromtimestamp(ohlcv_data[-1][0] / 1000) + timedelta(minutes=1)
                    
                    # Rate limiting
                    await asyncio.sleep(DATA_COLLECTION['rate_limit_delay'])
                    
                except Exception as e:
                    logging.error(f"    Error collecting perpetual data batch: {e}")
                    current_time += timedelta(hours=1)
                    await asyncio.sleep(2)
            
            logging.info(f"  Perpetual data collection complete: {total_records} total records")
            
        except Exception as e:
            logging.error(f"  Failed to collect perpetual data for {symbol}: {e}")
    
    async def _collect_funding_rate_data(self, exchange, pair_name, symbol, start_time, end_time):
        """Collect historical funding rate data."""
        logging.info(f"  Collecting funding rate data for {symbol}...")
        
        try:
            # Funding rates are published every 8 hours
            funding_times = []
            current = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            while current <= end_time:
                for hour in [0, 8, 16]:  # Funding times
                    funding_time = current.replace(hour=hour)
                    if start_time <= funding_time <= end_time:
                        funding_times.append(funding_time)
                current += timedelta(days=1)
            
            total_records = 0
            
            # Try to get historical funding rates (may be limited by exchange)
            try:
                since = int(start_time.timestamp() * 1000)
                funding_history = await exchange.fetch_funding_rate_history(symbol, since=since)
                
                if funding_history:
                    records_added = self._store_funding_rate_data(pair_name, funding_history)
                    total_records += records_added
                    logging.info(f"    Stored {records_added} historical funding rate records")
                else:
                    logging.warning(f"    No historical funding rate data available for {symbol}")
                    
            except Exception as e:
                logging.warning(f"    Historical funding rates not available: {e}")
                # Fall back to current funding rate only
                try:
                    current_funding = await exchange.fetch_funding_rate(symbol)
                    if current_funding:
                        records_added = self._store_current_funding_rate(pair_name, current_funding)
                        total_records += records_added
                        logging.info(f"    Stored current funding rate")
                except Exception as e2:
                    logging.error(f"    Failed to get current funding rate: {e2}")
            
            logging.info(f"  Funding rate collection complete: {total_records} records")
            
        except Exception as e:
            logging.error(f"  Failed to collect funding rate data for {symbol}: {e}")
    
    async def _get_mark_prices(self, exchange, symbol, ohlcv_data):
        """Try to get mark price data (may not be available for historical data)."""
        try:
            # This might not work for historical data, but we can try
            current_mark = await exchange.fetch_ticker(symbol)
            if 'markPrice' in current_mark:
                # For historical data, we'll approximate using close prices
                return [current_mark['markPrice']] * len(ohlcv_data)
        except:
            pass
        return [None] * len(ohlcv_data)
    
    def _store_spot_data(self, pair_name, ohlcv_data):
        """Store spot OHLCV data in database."""
        session = self.Session()
        records_added = 0
        
        try:
            for data in ohlcv_data:
                # Check if record already exists
                timestamp = datetime.fromtimestamp(data[0] / 1000)
                existing = session.query(SpotOHLCV).filter_by(
                    symbol=pair_name, timestamp=timestamp
                ).first()
                
                if not existing:
                    spot_record = SpotOHLCV(
                        symbol=pair_name,
                        timestamp=timestamp,
                        open=data[1],
                        high=data[2],
                        low=data[3],
                        close=data[4],
                        volume=data[5]
                    )
                    session.add(spot_record)
                    records_added += 1
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            logging.error(f"Error storing spot data: {e}")
        finally:
            session.close()
        
        return records_added
    
    def _store_perpetual_data(self, pair_name, ohlcv_data, mark_prices):
        """Store perpetual OHLCV data in database."""
        session = self.Session()
        records_added = 0
        
        try:
            for i, data in enumerate(ohlcv_data):
                timestamp = datetime.fromtimestamp(data[0] / 1000)
                existing = session.query(PerpetualOHLCV).filter_by(
                    symbol=pair_name, timestamp=timestamp
                ).first()
                
                if not existing:
                    perp_record = PerpetualOHLCV(
                        symbol=pair_name,
                        timestamp=timestamp,
                        open=data[1],
                        high=data[2],
                        low=data[3],
                        close=data[4],
                        volume=data[5],
                        mark_price=mark_prices[i] if i < len(mark_prices) else None,
                        index_price=None  # Will be populated later if available
                    )
                    session.add(perp_record)
                    records_added += 1
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            logging.error(f"Error storing perpetual data: {e}")
        finally:
            session.close()
        
        return records_added
    
    def _store_funding_rate_data(self, pair_name, funding_data):
        """Store funding rate data in database."""
        session = self.Session()
        records_added = 0
        
        try:
            for data in funding_data:
                timestamp = datetime.fromtimestamp(data['timestamp'] / 1000)
                existing = session.query(FundingRate).filter_by(
                    symbol=pair_name, timestamp=timestamp
                ).first()
                
                if not existing:
                    funding_record = FundingRate(
                        symbol=pair_name,
                        timestamp=timestamp,
                        funding_rate=data.get('fundingRate', 0),
                        predicted_rate=data.get('predictedRate'),
                        perpetual_price=data.get('markPrice'),
                        spot_price=data.get('indexPrice'),
                        basis_bps=None  # Will calculate later
                    )
                    session.add(funding_record)
                    records_added += 1
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            logging.error(f"Error storing funding rate data: {e}")
        finally:
            session.close()
        
        return records_added
    
    def _store_current_funding_rate(self, pair_name, funding_data):
        """Store current funding rate data."""
        session = self.Session()
        
        try:
            timestamp = datetime.fromtimestamp(funding_data['timestamp'] / 1000)
            existing = session.query(FundingRate).filter_by(
                symbol=pair_name, timestamp=timestamp
            ).first()
            
            if not existing:
                funding_record = FundingRate(
                    symbol=pair_name,
                    timestamp=timestamp,
                    funding_rate=funding_data.get('fundingRate', 0),
                    predicted_rate=funding_data.get('predictedRate'),
                    perpetual_price=funding_data.get('markPrice'),
                    spot_price=funding_data.get('indexPrice'),
                    basis_bps=None
                )
                session.add(funding_record)
                session.commit()
                return 1
            
        except Exception as e:
            session.rollback()
            logging.error(f"Error storing current funding rate: {e}")
        finally:
            session.close()
        
        return 0

async def collect_6_months_data():
    """Main function to collect 6 months of historical data."""
    collector = HistoricalDataCollector()
    await collector.collect_historical_data(days_back=180)

if __name__ == '__main__':
    asyncio.run(collect_6_months_data())
