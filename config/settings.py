import os
from pathlib import Path

# --- Project Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# --- Database Configuration ---
DATABASE_PATH = f"sqlite:///{PROJECT_ROOT / 'funding_rate_data.db'}"

# --- Exchange Configuration ---
EXCHANGE = 'bybit'

# --- Trading Pairs Configuration ---
TRADING_PAIRS = {
    'BTC/USDT': {
        'perpetual': 'BTC/USDT:USDT',
        'spot': 'BTC/USDT',
        'min_position_size': 0.001,
        'tick_size': 0.01
    },
    'ETH/USDT': {
        'perpetual': 'ETH/USDT:USDT', 
        'spot': 'ETH/USDT',
        'min_position_size': 0.01,
        'tick_size': 0.01
    },
    'SOL/USDT': {
        'perpetual': 'SOL/USDT:USDT',
        'spot': 'SOL/USDT', 
        'min_position_size': 0.1,
        'tick_size': 0.001
    }
}

# --- Data Collection Configuration ---
DATA_COLLECTION = {
    'interval': '1m',  # 1-minute candles
    'lookback_days': 30,  # Default historical data collection
    'funding_rate_interval': 8,  # Funding rates every 8 hours
    'max_retries': 3,
    'retry_delay': 5,  # seconds
}

# --- Funding Rate Configuration ---
FUNDING_RATE = {
    'collection_times': ['00:00', '08:00', '16:00'],  # UTC times
    'threshold_high': 0.01,  # 1% (very high funding rate)
    'threshold_low': -0.01,  # -1% (very negative funding rate)
    'annual_periods': 1095,  # 365 * 3 (funding every 8 hours)
}

# --- Backtesting Configuration ---
BACKTESTING = {
    'initial_capital': 100000,  # $100,000 starting capital
    'max_position_size': 0.1,  # 10% of capital per position
    'transaction_costs': {
        'perpetual_taker': 0.0006,  # 0.06% taker fee
        'spot_taker': 0.001,  # 0.1% taker fee
        'funding_cost': 0.0,  # No additional funding cost modeling
    },
    'risk_limits': {
        'max_drawdown': 0.2,  # 20% max drawdown
        'position_timeout': 24,  # Close position after 24 hours if not profitable
        'basis_threshold': 0.05,  # 5% basis difference stop-loss
    }
}

# --- Strategy Configuration ---
STRATEGY = {
    'funding_rate_arbitrage': {
        'entry_threshold': 0.005,  # 0.5% funding rate threshold
        'exit_threshold': 0.001,  # 0.1% funding rate threshold for exit
        'rebalance_frequency': '8h',  # Rebalance every 8 hours
        'hedge_ratio': 1.0,  # 1:1 hedge ratio
    }
}

# --- Risk Management ---
RISK_MANAGEMENT = {
    'var_confidence': 0.95,  # 95% VaR confidence
    'lookback_period': 252,  # 252 trading days for risk calculations
    'stress_test_scenarios': 5,  # Number of stress test scenarios
    'correlation_threshold': 0.8,  # Position correlation limit
}

# --- API Configuration ---
API_CONFIG = {
    'rate_limit': True,
    'sandbox': False,
    'timeout': 30000,  # 30 seconds
    'retry_on_error': True,
}

# --- Logging Configuration ---
LOGGING = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': LOGS_DIR / 'funding_rate_arbitrage.log',
    'max_size': 50 * 1024 * 1024,  # 50MB
    'backup_count': 5,
}

# --- Environment Variables ---
def get_api_credentials():
    """Get API credentials from environment variables."""
    return {
        'apiKey': os.getenv('BYBIT_API_KEY'),
        'secret': os.getenv('BYBIT_API_SECRET'),
        'testnet': os.getenv('BYBIT_TESTNET', 'False').lower() == 'true',
    }
