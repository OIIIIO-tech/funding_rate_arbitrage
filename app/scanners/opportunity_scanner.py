#!/usr/bin/env python3
"""
Live Opportunity Scanner for Funding Rate Arbitrage

This scanner monitors real-time funding rates, spot-futures spreads, and identifies
profitable arbitrage opportunities across different trading pairs on Bybit.
"""

import ccxt.async_support as ccxt
import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.models.funding_rate_models import Base, PerpetualOHLCV, SpotOHLCV, FundingRate
from config.settings import DATABASE_PATH, TRADING_PAIRS, get_api_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/opportunity_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ArbitrageOpportunity:
    """Represents a funding rate arbitrage opportunity."""
    symbol: str
    opportunity_type: str  # 'long_funding', 'short_funding', 'basis_arbitrage'
    
    # Market data
    spot_price: float
    futures_price: float
    funding_rate: float
    next_funding_time: datetime
    
    # Opportunity metrics
    basis_bps: float  # Basis in basis points
    annual_funding_rate: float  # Annualized funding rate %
    profit_potential: float  # Expected profit %
    risk_score: float  # Risk assessment (1-10)
    
    # Trade details
    recommended_action: str  # 'LONG_SPOT_SHORT_PERP' or 'SHORT_SPOT_LONG_PERP'
    entry_confidence: str  # 'HIGH', 'MEDIUM', 'LOW'
    min_capital: float  # Minimum recommended capital
    
    # Additional data
    volume_24h: float
    bid_ask_spread: float
    funding_history: List[float]  # Recent funding rates
    timestamp: datetime

class OpportunityScanner:
    def __init__(self):
        # Database setup
        self.engine = create_engine(DATABASE_PATH)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Exchange setup
        credentials = get_api_credentials()
        self.exchange_config = {
            'apiKey': credentials['apiKey'],
            'secret': credentials['secret'],
            'testnet': credentials['testnet'],
            'enableRateLimit': True,
        }
        
        # Scanner configuration
        self.config = {
            'min_funding_rate': 0.0001,  # 0.01% (3.65% annually)
            'min_basis_bps': 5,  # 5 basis points
            'max_risk_score': 7,  # Maximum acceptable risk
            'min_volume_24h': 1000000,  # $1M minimum daily volume
            'max_spread_bps': 10,  # Maximum bid-ask spread
            'scan_interval': 30,  # Scan every 30 seconds
        }
        
        # Store recent opportunities for trend analysis
        self.recent_opportunities = []
        self.market_cache = {}
        
    async def start_scanning(self):
        """Start the live opportunity scanning process."""
        logger.info("🔍 Starting live funding rate arbitrage scanner...")
        logger.info(f"📊 Monitoring pairs: {list(TRADING_PAIRS.keys())}")
        logger.info(f"⚙️  Scan interval: {self.config['scan_interval']} seconds")
        
        while True:
            try:
                opportunities = await self.scan_opportunities()
                await self.process_opportunities(opportunities)
                await asyncio.sleep(self.config['scan_interval'])
                
            except KeyboardInterrupt:
                logger.info("🛑 Scanner stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in scanning loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def scan_opportunities(self) -> List[ArbitrageOpportunity]:
        """Scan for current arbitrage opportunities."""
        opportunities = []
        
        async with ccxt.bybit(self.exchange_config) as exchange:
            await exchange.load_markets()
            
            for pair_name, pair_info in TRADING_PAIRS.items():
                try:
                    opportunity = await self._analyze_pair(exchange, pair_name, pair_info)
                    if opportunity:
                        opportunities.append(opportunity)
                        
                except Exception as e:
                    logger.error(f"Error analyzing {pair_name}: {e}")
                    continue
        
        return opportunities
    
    async def _analyze_pair(self, exchange, pair_name: str, pair_info: dict) -> Optional[ArbitrageOpportunity]:
        """Analyze a specific trading pair for arbitrage opportunities."""
        try:
            # Get current market data
            spot_symbol = pair_info['spot']
            futures_symbol = pair_info['perpetual']
            
            # Fetch spot data
            exchange.options['defaultType'] = 'spot'
            spot_ticker = await exchange.fetch_ticker(spot_symbol)
            spot_orderbook = await exchange.fetch_order_book(spot_symbol, limit=5)
            
            # Fetch futures data
            exchange.options['defaultType'] = 'future'
            futures_ticker = await exchange.fetch_ticker(futures_symbol)
            futures_orderbook = await exchange.fetch_order_book(futures_symbol, limit=5)
            funding_rate_info = await exchange.fetch_funding_rate(futures_symbol)
            
            # Debug: Log the raw data to understand structure
            logger.debug(f"Funding rate info for {pair_name}: {funding_rate_info}")
            
            # Calculate metrics with error handling
            spot_price = float(spot_ticker['last'])
            futures_price = float(futures_ticker['last'])
            funding_rate = float(funding_rate_info['fundingRate'])
            
            # Handle funding datetime (might be string or timestamp)
            funding_datetime = funding_rate_info.get('fundingDatetime')
            if funding_datetime is None:
                # Use current time + 8 hours as fallback
                next_funding = datetime.utcnow() + timedelta(hours=8)
            elif isinstance(funding_datetime, str):
                # Parse ISO string
                from datetime import datetime as dt
                try:
                    next_funding = dt.fromisoformat(funding_datetime.replace('Z', '+00:00'))
                except ValueError:
                    # Fallback for different string formats
                    next_funding = datetime.utcnow() + timedelta(hours=8)
            else:
                # Convert timestamp
                next_funding = datetime.fromtimestamp(int(funding_datetime) / 1000)
            
            # Calculate basis (futures premium/discount)
            basis = futures_price - spot_price
            basis_bps = (basis / spot_price) * 10000  # Convert to basis points
            
            # Calculate annualized funding rate
            annual_funding_rate = funding_rate * 365 * 3 * 100  # 3 times daily, to percentage
            
            # Calculate bid-ask spreads
            spot_spread = ((spot_orderbook['asks'][0][0] - spot_orderbook['bids'][0][0]) / spot_price) * 10000
            futures_spread = ((futures_orderbook['asks'][0][0] - futures_orderbook['bids'][0][0]) / futures_price) * 10000
            avg_spread = (spot_spread + futures_spread) / 2
            
            # Get volume data
            volume_24h = futures_ticker.get('quoteVolume', 0)
            
            # Get funding rate history
            funding_history = await self._get_funding_history(pair_name)
            
            # Determine if this is an opportunity
            opportunity = self._evaluate_opportunity(
                pair_name, spot_price, futures_price, funding_rate, next_funding,
                basis_bps, annual_funding_rate, volume_24h, avg_spread, funding_history
            )
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error analyzing pair {pair_name}: {e}")
            return None
    
    def _evaluate_opportunity(
        self, 
        symbol: str,
        spot_price: float,
        futures_price: float,
        funding_rate: float,
        next_funding: datetime,
        basis_bps: float,
        annual_funding_rate: float,
        volume_24h: float,
        avg_spread: float,
        funding_history: List[float]
    ) -> Optional[ArbitrageOpportunity]:
        """Evaluate whether current market conditions present an arbitrage opportunity."""
        
        # Check minimum thresholds
        if abs(funding_rate) < self.config['min_funding_rate']:
            return None
            
        if volume_24h < self.config['min_volume_24h']:
            return None
            
        if avg_spread > self.config['max_spread_bps']:
            return None
        
        # Determine opportunity type and action
        if funding_rate > 0:
            # Positive funding: shorts pay longs
            # Strategy: Long spot, short perpetual (collect funding)
            opportunity_type = 'long_funding'
            recommended_action = 'LONG_SPOT_SHORT_PERP'
            profit_potential = abs(annual_funding_rate)
        else:
            # Negative funding: longs pay shorts
            # Strategy: Short spot, long perpetual (collect funding)
            opportunity_type = 'short_funding'  
            recommended_action = 'SHORT_SPOT_LONG_PERP'
            profit_potential = abs(annual_funding_rate)
        
        # Calculate risk score (1-10, lower is better)
        risk_score = self._calculate_risk_score(
            funding_rate, basis_bps, avg_spread, volume_24h, funding_history
        )
        
        if risk_score > self.config['max_risk_score']:
            return None
        
        # Determine entry confidence
        confidence = self._determine_confidence(
            abs(funding_rate), abs(basis_bps), risk_score, funding_history
        )
        
        # Calculate minimum capital (based on spreads and fees)
        min_capital = self._calculate_min_capital(spot_price, avg_spread)
        
        return ArbitrageOpportunity(
            symbol=symbol,
            opportunity_type=opportunity_type,
            spot_price=spot_price,
            futures_price=futures_price,
            funding_rate=funding_rate,
            next_funding_time=next_funding,
            basis_bps=basis_bps,
            annual_funding_rate=annual_funding_rate,
            profit_potential=profit_potential,
            risk_score=risk_score,
            recommended_action=recommended_action,
            entry_confidence=confidence,
            min_capital=min_capital,
            volume_24h=volume_24h,
            bid_ask_spread=avg_spread,
            funding_history=funding_history,
            timestamp=datetime.utcnow()
        )
    
    def _calculate_risk_score(
        self, 
        funding_rate: float, 
        basis_bps: float, 
        spread: float, 
        volume: float,
        funding_history: List[float]
    ) -> float:
        """Calculate risk score for the opportunity (1-10, lower is better)."""
        risk_score = 1.0
        
        # Funding rate volatility risk
        if funding_history:
            funding_std = np.std(funding_history) if len(funding_history) > 1 else 0
            if funding_std > 0.0005:  # High volatility
                risk_score += 2
            elif funding_std > 0.0002:
                risk_score += 1
        
        # Extreme funding rate risk
        if abs(funding_rate) > 0.002:  # Very high funding rate
            risk_score += 2
        elif abs(funding_rate) > 0.001:
            risk_score += 1
        
        # Basis risk (mean reversion)
        if abs(basis_bps) > 50:  # Large basis
            risk_score += 1.5
        elif abs(basis_bps) > 20:
            risk_score += 0.5
        
        # Liquidity risk
        if volume < 5000000:  # Low volume
            risk_score += 1.5
        elif volume < 2000000:
            risk_score += 2.5
        
        # Spread risk
        if spread > 8:
            risk_score += 1
        elif spread > 15:
            risk_score += 2
        
        return min(risk_score, 10.0)
    
    def _determine_confidence(
        self, 
        abs_funding_rate: float, 
        abs_basis_bps: float, 
        risk_score: float,
        funding_history: List[float]
    ) -> str:
        """Determine confidence level for the opportunity."""
        score = 0
        
        # High funding rate
        if abs_funding_rate > 0.0015:
            score += 3
        elif abs_funding_rate > 0.0008:
            score += 2
        elif abs_funding_rate > 0.0003:
            score += 1
        
        # Consistent funding direction
        if funding_history and len(funding_history) >= 3:
            recent_rates = funding_history[-3:]
            if all(r > 0 for r in recent_rates) or all(r < 0 for r in recent_rates):
                score += 2
        
        # Low risk
        if risk_score < 3:
            score += 2
        elif risk_score < 5:
            score += 1
        
        # Determine confidence
        if score >= 6:
            return 'HIGH'
        elif score >= 4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _calculate_min_capital(self, price: float, spread_bps: float) -> float:
        """Calculate minimum recommended capital."""
        # Base minimum to cover spreads and fees
        base_min = 10000  # $10k base
        
        # Adjust for spreads (need more capital for wider spreads)
        spread_multiplier = 1 + (spread_bps / 100)
        
        return base_min * spread_multiplier
    
    async def _get_funding_history(self, symbol: str) -> List[float]:
        """Get recent funding rate history from database."""
        session = self.Session()
        try:
            recent_rates = session.query(FundingRate.funding_rate)\
                .filter_by(symbol=symbol)\
                .order_by(FundingRate.timestamp.desc())\
                .limit(10)\
                .all()
            
            return [rate[0] for rate in recent_rates if rate[0] is not None]
        
        except Exception as e:
            logger.error(f"Error getting funding history for {symbol}: {e}")
            return []
        finally:
            session.close()
    
    async def process_opportunities(self, opportunities: List[ArbitrageOpportunity]):
        """Process and display found opportunities."""
        if not opportunities:
            logger.info("📊 No arbitrage opportunities found at current thresholds")
            return
        
        # Sort by profit potential
        opportunities.sort(key=lambda x: x.profit_potential, reverse=True)
        
        logger.info(f"\n🎯 FOUND {len(opportunities)} ARBITRAGE OPPORTUNITIES")
        logger.info("=" * 80)
        
        for i, opp in enumerate(opportunities, 1):
            await self._display_opportunity(i, opp)
            
        # Store opportunities for trend analysis
        self.recent_opportunities.extend(opportunities)
        # Keep only last 100 opportunities
        self.recent_opportunities = self.recent_opportunities[-100:]
        
        # Save to database
        await self._save_opportunities(opportunities)
    
    async def _display_opportunity(self, rank: int, opp: ArbitrageOpportunity):
        """Display a formatted opportunity."""
        # Handle timezone-aware datetime
        now = datetime.utcnow()
        if opp.next_funding_time.tzinfo is not None:
            # Convert to UTC if timezone-aware
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)
        
        time_to_funding = opp.next_funding_time - now
        hours_to_funding = time_to_funding.total_seconds() / 3600
        
        # Format colors for terminal output
        confidence_color = {
            'HIGH': '🟢',
            'MEDIUM': '🟡', 
            'LOW': '🔴'
        }
        
        logger.info(f"\n{rank}. {confidence_color.get(opp.entry_confidence, '⚪')} {opp.symbol} - {opp.opportunity_type.upper()}")
        logger.info(f"   💰 Profit Potential: {opp.profit_potential:+.2f}% annually")
        logger.info(f"   📈 Funding Rate: {opp.funding_rate:.6f} ({opp.annual_funding_rate:+.2f}% annual)")
        logger.info(f"   💲 Spot: ${opp.spot_price:,.2f} | Futures: ${opp.futures_price:,.2f}")
        logger.info(f"   📊 Basis: {opp.basis_bps:+.1f} bps | Spread: {opp.bid_ask_spread:.1f} bps")
        logger.info(f"   🎯 Action: {opp.recommended_action}")
        logger.info(f"   ⚠️  Risk Score: {opp.risk_score:.1f}/10 | Confidence: {opp.entry_confidence}")
        logger.info(f"   💵 Min Capital: ${opp.min_capital:,.0f}")
        logger.info(f"   📅 Next Funding: {hours_to_funding:.1f}h")
        logger.info(f"   📈 24h Volume: ${opp.volume_24h:,.0f}")
    
    async def _save_opportunities(self, opportunities: List[ArbitrageOpportunity]):
        """Save opportunities to database for historical analysis."""
        # This could be expanded to save opportunities to a dedicated table
        session = self.Session()
        try:
            # For now, we'll log to file
            opportunities_data = []
            for opp in opportunities:
                opportunities_data.append({
                    'timestamp': opp.timestamp.isoformat(),
                    'symbol': opp.symbol,
                    'funding_rate': opp.funding_rate,
                    'annual_rate': opp.annual_funding_rate,
                    'profit_potential': opp.profit_potential,
                    'risk_score': opp.risk_score,
                    'confidence': opp.entry_confidence,
                    'action': opp.recommended_action
                })
            
            # Save to JSON log file
            with open('logs/opportunities.json', 'a') as f:
                for opp_data in opportunities_data:
                    f.write(json.dumps(opp_data) + '\n')
                    
        except Exception as e:
            logger.error(f"Error saving opportunities: {e}")
        finally:
            session.close()

# Import numpy for calculations
try:
    import numpy as np
except ImportError:
    logger.warning("NumPy not available, using basic calculations")
    # Simple fallback for standard deviation
    def np_std(values):
        if len(values) <= 1:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    class np:
        @staticmethod
        def std(values):
            return np_std(values)

async def main():
    """Main function to run the opportunity scanner."""
    scanner = OpportunityScanner()
    await scanner.start_scanning()

if __name__ == '__main__':
    asyncio.run(main())
