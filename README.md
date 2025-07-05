# Funding Rate Arbitrage Backtest and Simulation

A comprehensive system for collecting, analyzing, and backtesting funding rate arbitrage opportunities across cryptocurrency exchanges.

## Overview

Funding rate arbitrage exploits the periodic funding payments between perpetual futures and spot positions. This project focuses on collecting and analyzing data from Bybit to identify profitable funding rate arbitrage opportunities.

## Features

- **Historical Data Collection**: Automated collection of OHLCV data, funding rates, and spot/perpetual prices
- **Real-time Monitoring**: Live tracking of funding rates and price differences
- **Backtesting Engine**: Comprehensive backtesting framework for funding rate strategies
- **Risk Analysis**: Detailed risk metrics and performance analytics
- **Database Storage**: Efficient storage and retrieval of historical data

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

### Data Collection
```bash
# Collect historical data
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

### Funding Rate Arbitrage
1. **Long Perpetual + Short Spot**: When funding rate is positive (longs pay shorts)
2. **Short Perpetual + Long Spot**: When funding rate is negative (shorts pay longs)
3. **Delta Neutral**: Maintain market-neutral position to capture funding payments

### Key Metrics
- **Funding Rate**: Percentage charged every 8 hours
- **Basis**: Price difference between perpetual and spot
- **Carrying Cost**: Cost of maintaining the arbitrage position
- **Net APY**: Annualized return after all costs

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
