from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint, Index
from datetime import datetime

Base = declarative_base()

class PerpetualOHLCV(Base):
    """Perpetual futures OHLCV data model."""
    __tablename__ = 'perpetual_ohlcv'

    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)  # e.g., 'BTC/USDT:USDT'
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    # Additional perpetual-specific fields
    mark_price = Column(Float)  # Mark price used for funding calculations
    index_price = Column(Float)  # Underlying index price
    
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', name='_perpetual_symbol_timestamp_uc'),
        Index('idx_perpetual_symbol_time', 'symbol', 'timestamp'),
    )

    def __repr__(self):
        return f'<PerpetualOHLCV(symbol={self.symbol}, timestamp={self.timestamp}, close={self.close})>'


class SpotOHLCV(Base):
    """Spot market OHLCV data model."""
    __tablename__ = 'spot_ohlcv'

    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)  # e.g., 'BTC/USDT'
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', name='_spot_symbol_timestamp_uc'),
        Index('idx_spot_symbol_time', 'symbol', 'timestamp'),
    )

    def __repr__(self):
        return f'<SpotOHLCV(symbol={self.symbol}, timestamp={self.timestamp}, close={self.close})>'


class FundingRate(Base):
    """Funding rate data model."""
    __tablename__ = 'funding_rates'

    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)  # e.g., 'BTC/USDT:USDT'
    timestamp = Column(DateTime, nullable=False)  # Funding timestamp
    funding_rate = Column(Float, nullable=False)  # Current funding rate
    predicted_rate = Column(Float)  # Next predicted funding rate
    
    # Basis and spread information
    perpetual_price = Column(Float)  # Perpetual price at funding time
    spot_price = Column(Float)  # Spot price at funding time
    basis_bps = Column(Float)  # Basis in basis points
    
    # Volume and liquidity metrics
    perpetual_volume_24h = Column(Float)  # 24h perpetual volume
    spot_volume_24h = Column(Float)  # 24h spot volume
    open_interest = Column(Float)  # Open interest in perpetual
    
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', name='_funding_symbol_timestamp_uc'),
        Index('idx_funding_symbol_time', 'symbol', 'timestamp'),
        Index('idx_funding_rate', 'funding_rate'),
    )

    def __repr__(self):
        return f'<FundingRate(symbol={self.symbol}, timestamp={self.timestamp}, rate={self.funding_rate:.4f})>'

    @property
    def annual_rate(self):
        """Calculate annualized funding rate (365 * 3 periods per day)."""
        return self.funding_rate * 365 * 3

    @property
    def basis_percentage(self):
        """Calculate basis as percentage."""
        if self.spot_price and self.spot_price > 0:
            return ((self.perpetual_price - self.spot_price) / self.spot_price) * 100
        return None


class ArbitrageOpportunity(Base):
    """Detected arbitrage opportunities model."""
    __tablename__ = 'arbitrage_opportunities'

    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Opportunity details
    funding_rate = Column(Float, nullable=False)
    annual_funding_rate = Column(Float, nullable=False)
    basis_bps = Column(Float, nullable=False)
    
    # Prices at detection
    perpetual_price = Column(Float, nullable=False)
    spot_price = Column(Float, nullable=False)
    
    # Opportunity metrics
    expected_profit_bps = Column(Float)  # Expected profit in basis points
    risk_score = Column(Float)  # Risk assessment score (0-100)
    liquidity_score = Column(Float)  # Liquidity assessment score (0-100)
    
    # Strategy recommendation
    strategy = Column(String)  # 'long_perp_short_spot' or 'short_perp_long_spot'
    recommended_size = Column(Float)  # Recommended position size in USD
    
    # Execution tracking
    executed = Column(Integer, default=0)  # 0: not executed, 1: executed, -1: expired
    execution_timestamp = Column(DateTime)
    actual_profit = Column(Float)  # Actual profit if executed
    
    __table_args__ = (
        Index('idx_opportunity_symbol_time', 'symbol', 'detected_at'),
        Index('idx_opportunity_funding_rate', 'funding_rate'),
        Index('idx_opportunity_executed', 'executed'),
    )

    def __repr__(self):
        return f'<ArbitrageOpportunity(symbol={self.symbol}, funding_rate={self.funding_rate:.4f}, strategy={self.strategy})>'


class BacktestResult(Base):
    """Backtest results storage model."""
    __tablename__ = 'backtest_results'

    id = Column(Integer, primary_key=True)
    strategy_name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Performance metrics
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    annual_return = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)
    sharpe_ratio = Column(Float)
    
    # Trade statistics
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    avg_trade_return = Column(Float)
    avg_trade_duration = Column(Float)  # in hours
    
    # Risk metrics
    volatility = Column(Float)
    var_95 = Column(Float)  # 95% Value at Risk
    
    # Strategy-specific metrics
    avg_funding_captured = Column(Float)  # Average funding rate captured
    total_funding_payments = Column(Float)  # Total funding payments received
    basis_risk_realized = Column(Float)  # Realized basis risk
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_backtest_strategy_symbol', 'strategy_name', 'symbol'),
        Index('idx_backtest_dates', 'start_date', 'end_date'),
    )

    def __repr__(self):
        return f'<BacktestResult(strategy={self.strategy_name}, symbol={self.symbol}, return={self.total_return:.2%})>'
