import ccxt.async_support as ccxt
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime

from app.models.funding_rate_models import Base, PerpetualOHLCV, SpotOHLCV, FundingRate
from config.settings import DATABASE_PATH, TRADING_PAIRS, get_api_credentials

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def fetch_ohlcv(exchange, symbol, timeframe='1m', since=None):
    
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=since)
        return ohlcv
    except ccxt.BaseError as e:
        logging.error(f"Error fetching OHLCV for {symbol}: {e}")
        return None

async def collect_data():
    """Collect and store OHLCV and funding rate data."""

    # Create database session
    engine = create_engine(DATABASE_PATH)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    api_credentials = get_api_credentials()
    exchange = ccxt.bybit({
        "apiKey": api_credentials['apiKey'],
        "secret": api_credentials['secret'],
        "enableRateLimit": True,
    })
    
    # Collect data for each trading pair
    async with exchange:
        for pair, info in TRADING_PAIRS.items():
            logging.info(f"Collecting data for {pair}")
            try:
                # Fetch Spot OHLCV
                spot_ohlcv = await fetch_ohlcv(exchange, info['spot'], '1m')
                # Fetch Perpetual OHLCV
                perp_ohlcv = await fetch_ohlcv(exchange, info['perpetual'], '1m')
                # Fetch Funding Rate
                # Example using place holder function (implement funding rate fetch logic)
                funding_rate_info = await fetch_funding_rate(exchange, info['perpetual'])
                
                # Store in database
                store_ohlcv_and_funding(Session, pair, spot_ohlcv, perp_ohlcv, funding_rate_info)

            except Exception as e:
                logging.error(f"Failed to collect data for {pair}: {e}")

async def fetch_funding_rate(exchange, symbol):
    """Fetch the funding rate for a given symbol."""
    try:
        # Placeholder: Replace with actual logic to get funding rate and additional data
        funding_rate = exchange.fetchFundingRate(symbol)
        return funding_rate
    except ccxt.BaseError as e:
        logging.error(f"Error fetching funding rate for {symbol}: {e}")
        return None


def store_ohlcv_and_funding(Session, pair_name, spot_ohlcv_data, perp_ohlcv_data, funding_rate_info):
    """Store collected data in the database."""
    session = Session()
    try:
        for data in spot_ohlcv_data:
            spot_ohlcv = SpotOHLCV(
                symbol=pair_name,
                timestamp=datetime.fromtimestamp(data[0] / 1000),
                open=data[1],
                high=data[2],
                low=data[3],
                close=data[4],
                volume=data[5]
            )
            session.add(spot_ohlcv)

        for data in perp_ohlcv_data:
            perp_ohlcv = PerpetualOHLCV(
                symbol=pair_name,
                timestamp=datetime.fromtimestamp(data[0] / 1000),
                open=data[1],
                high=data[2],
                low=data[3],
                close=data[4],
                volume=data[5],
                mark_price=None,  # Replace with real mark price
                index_price=None  # Replace with real index price
            )
            session.add(perp_ohlcv)

        # Placeholder: Use real data instead
        funding_rate = FundingRate(
            symbol=pair_name,
            timestamp=datetime.now(),  # Replace with real funding timestamp
            funding_rate=funding_rate_info.get('funding_rate', 0),  # Replace with real data
            perpetual_price=None,  # Replace with real perpetual price
            spot_price=None,  # Replace with real spot price
            basis_bps=None  # Replace with calculated basis
        )
        session.add(funding_rate)

        session.commit()
        logging.info(f"Data for {pair_name} stored successfully.")

    except Exception as e:
        session.rollback()
        logging.error(f"Failed to store data for {pair_name}: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    asyncio.run(collect_data())

# Note: This is a draft setup, replace placeholders with actual funding rate retrieval logic.
