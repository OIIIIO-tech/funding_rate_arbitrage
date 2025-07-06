# Funding Rate Arbitrage Backtest and Simulation

A comprehensive system for collecting, analyzing, and backtesting funding rate arbitrage opportunities across cryptocurrency exchanges.

## Overview

Funding rate arbitrage exploits the periodic funding payments between perpetual futures and spot positions. This project focuses on collecting and analyzing data from Bybit to identify profitable funding rate arbitrage opportunities.

## Features

- **🔍 Live Opportunity Scanner**: Real-time detection of profitable funding rate arbitrage opportunities
- **📊 Comprehensive Market Analysis**: Automated analysis of spot-futures spreads, funding rates, and basis
- **⚡ Multiple Scanning Modes**: Normal, aggressive, conservative, and ultra-aggressive scanning strategies
- **🎯 Risk Assessment**: Automated risk scoring (1-10 scale) with confidence levels
- **💰 Profit Calculation**: Real-time profit potential with annualized funding rate percentages
- **📈 Historical Data Collection**: Automated collection of OHLCV data, funding rates, and spot/perpetual prices
- **🔄 Real-time Monitoring**: Live tracking of funding rates and price differences
- **🧪 Backtesting Engine**: Comprehensive backtesting framework for funding rate strategies
- **📋 Database Inspection**: Tools to analyze stored historical data
- **💾 Database Storage**: Efficient storage and retrieval of historical data

## Trading Pairs

- BTC/USDT (Bitcoin)
- ETH/USDT (Ethereum)  
- SOL/USDT (Solana)

## Data Collection

### Perpetual Futures Data
- 1-minute OHLCV candles
- Funding rates (every 8 hours)
- Mark prices
- Index prices

### Spot Market Data
- 1-minute OHLCV candles
- Real-time prices
- Volume metrics

## Project Structure

```
funding_rate_arbitrage/
├── app/
│   ├── data_collectors/     # Data collection modules
│   ├── scanners/           # Live opportunity scanners
│   ├── models/             # Database models
│   ├── database/           # Database connection and setup
│   ├── strategies/         # Funding rate arbitrage strategies
│   ├── backtesting/        # Backtesting engine
│   ├── analytics/          # Performance analytics
│   └── utils/              # Utility functions
├── tests/                  # Unit tests
├── docs/                   # Documentation
├── config/                 # Configuration files
├── main.py                 # Main application entry point
└── requirements.txt        # Python dependencies
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd funding_rate_arbitrage
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up the database:
```bash
python main.py setup
```

4. Configure API credentials in `.env` file

## Usage

### 🔍 Live Opportunity Scanner

**Quick Scan** (Single pass):
```bash
python scanner_dashboard.py --quick
```

**Live Monitoring** (Continuous scanning every 30 seconds):
```bash
python scanner_dashboard.py
```

**Scanning Modes**:
```bash
# Aggressive mode - Lower thresholds, more opportunities
python scanner_dashboard.py --aggressive

# Conservative mode - Higher thresholds, safer opportunities
python scanner_dashboard.py --conservative

# Ultra-aggressive - Maximum sensitivity
python scan_live_opportunities.py
```

**Utilities**:
```bash
# Test scanner functionality
python test_scanner.py

# Debug current market data
python debug_market_data.py

# Check database contents
python check_database.py

# Show scanner configuration
python scanner_dashboard.py --config
```

### 📈 Data Collection
```bash
# Collect comprehensive historical data
python main.py collect --historical --days 180

# Collect basic historical data
python main.py collect --days 30

# Start real-time data collection
python main.py collect --live
```

### Backtesting
```bash
# Run funding rate arbitrage backtest
python main.py backtest --strategy funding_rate --start 2024-01-01 --end 2024-12-31

# Backtest with custom parameters
python main.py backtest --strategy funding_rate --capital 100000 --max_position 0.1
```

### Analytics
```bash
# Generate performance report
python main.py analyze --strategy funding_rate --period 6m

# View funding rate history
python main.py view --data funding_rates --pair BTC/USDT
```

## Strategy Overview

### 🎯 Live Opportunity Detection

The scanner identifies two main types of funding rate arbitrage:

#### 🟢 **Long Funding Strategy** (Positive funding rates)
- **Action**: Buy spot + Sell perpetual futures
- **When**: Funding rate > 0 (shorts pay longs)
- **Profit**: Collect funding payments every 8 hours
- **Example**: If funding rate is +0.01% (3.65% annually), you earn payments

#### 🔴 **Short Funding Strategy** (Negative funding rates)
- **Action**: Sell spot + Buy perpetual futures  
- **When**: Funding rate < 0 (longs pay shorts)
- **Profit**: Collect funding payments every 8 hours
- **Example**: If funding rate is -0.01% (-3.65% annually), you earn payments

### Key Metrics
- **Funding Rate**: Percentage charged every 8 hours (3x daily)
- **Annual Rate**: Funding rate × 365 × 3 (annualized percentage)
- **Basis**: Price difference between perpetual and spot (in basis points)
- **Risk Score**: 1-10 scale based on volatility, spreads, and volume
- **Confidence**: HIGH/MEDIUM/LOW based on funding consistency and market conditions
- **Next Funding**: Time until next funding payment (every 8 hours: 00:00, 08:00, 16:00 UTC)

## Risk Management

- **Position Sizing**: Dynamic position sizing based on volatility
- **Stop Loss**: Automated stop-loss when basis exceeds threshold
- **Funding Rate Prediction**: ML models to predict funding rate changes
- **Liquidity Monitoring**: Real-time liquidity assessment

## Dependencies

- **ccxt**: Cryptocurrency exchange integration
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **SQLAlchemy**: Database ORM
- **matplotlib**: Data visualization
- **scikit-learn**: Machine learning for predictive models

## Configuration

### 🔧 Scanner Configuration

The opportunity scanner can be configured with different risk/reward profiles:

#### **Normal Mode** (Default)
- Min Funding Rate: 0.0001 (10.95% annually)
- Max Risk Score: 7/10
- Min Volume: $1,000,000
- Max Spread: 10 bps

#### **Aggressive Mode**
- Min Funding Rate: 0.00005 (1.83% annually) 
- Max Risk Score: 8/10
- Min Volume: $500,000
- Max Spread: 15 bps

#### **Conservative Mode**
- Min Funding Rate: 0.0002 (7.3% annually)
- Max Risk Score: 5/10
- Min Volume: $2,000,000
- Max Spread: 8 bps

#### **Ultra-Aggressive Mode**
- Min Funding Rate: 0.00003 (3.3% annually)
- Max Risk Score: 10/10
- Min Volume: $100,000
- Max Spread: 50 bps

### ⚙️ General Configuration

All trading pairs, risk parameters, and exchange settings can be configured in `config/settings.py`.

## License

This project is for educational and research purposes. Please ensure compliance with exchange terms of service and local regulations.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Disclaimer

This software is for educational purposes only. Trading cryptocurrencies involves substantial risk of loss. Past performance does not guarantee future results.
