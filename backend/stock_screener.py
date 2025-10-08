import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from alpaca_trade_api import TimeFrame
import pandas as pd
import numpy as np

try:
    import talib
    TALIB_AVAILABLE = True
    print("TA-Lib imported successfully")
except ImportError:
    TALIB_AVAILABLE = False
    print("TA-Lib not available, using pandas implementation")

load_dotenv()

API_KEY_ID = os.getenv("API_KEY_ID")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
url = "https://paper-api.alpaca.markets"
api = tradeapi.REST(API_KEY_ID, API_SECRET_KEY, url)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockScreener:
    def __init__(self):
        self.api = api
    
    def get_stock_universe(self):
        """Get basic stock universe from Alpaca"""
        try:
            # Get active assets
            assets = self.api.list_assets(status='active', asset_class='us_equity')
            
            # Filter for tradeable stocks
            stocks = []
            for asset in assets:
                if (asset.tradable and 
                    asset.exchange in ['NYSE', 'NASDAQ'] and
                    not asset.symbol.endswith('.') and  # Avoid class shares
                    len(asset.symbol) <= 5):  # Reasonable symbol length
                    stocks.append(asset.symbol)
            
            logger.info(f"Found {len(stocks)} tradeable stocks")
            return stocks[:500]  # Limit for testing, can expand later
            
        except Exception as e:
            logger.error(f"Error getting stock universe: {e}")
            return []
    
    def get_stock_data(self, symbol, days=100):
        """Get historical data for a stock"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            data = self.api.get_bars(
                symbol, 
                TimeFrame.Day,
                start=start_date.isoformat() + 'Z',
                end=end_date.isoformat() + 'Z'
            ).df
            
            return data
        except Exception as e:
            logger.warning(f"Could not get data for {symbol}: {e}")
            return None

    def calculate_technical_indicators(self, data):
        """Calculate technical indicators for screening"""
        if data is None or len(data) < 50:
            return None
            
        try:
            data['sma_20'] = data['close'].rolling(window=20).mean()
            data['sma_50'] = data['close'].rolling(window=50).mean()
            data['volume_avg_20'] = data['volume'].rolling(window=20).mean()
            
            # MACD indicators for MACD-specific scoring
            if TALIB_AVAILABLE:
                data['MACD'], data['Signal'], data['Hist'] = talib.MACD(
                    data['close'], fastperiod=12, slowperiod=26, signalperiod=9
                )
                data['RSI'] = talib.RSI(data['close'], timeperiod=14)
                data['ATR'] = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
                data['ADX'] = talib.ADX(data['high'], data['low'], data['close'], timeperiod=14)
            else:
                # Pandas fallback
                ema_12 = data['close'].ewm(span=12).mean()
                ema_26 = data['close'].ewm(span=26).mean()
                data['MACD'] = ema_12 - ema_26
                data['Signal'] = data['MACD'].ewm(span=9).mean()
                data['Hist'] = data['MACD'] - data['Signal']
                
                # Simple RSI calculation
                delta = data['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))
                
                # Simple ATR
                high_low = data['high'] - data['low']
                high_close = np.abs(data['high'] - data['close'].shift())
                low_close = np.abs(data['low'] - data['close'].shift())
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                data['ATR'] = true_range.rolling(window=14).mean()
            
            return data
        except Exception as e:
            logger.warning(f"Error calculating indicators: {e}")
            return None

    def apply_base_filters(self, symbol, data):
        """Apply basic filtering criteria"""
        if data is None or len(data) < 50:
            return False, "Insufficient data"
        
        try:
            latest = data.iloc[-1]
            prev_20 = data.iloc[-20:]
            
            # Basic price and volume filters
            if latest['close'] < 5:
                return False, "Price too low"
            
            if latest['volume'] < 100000:
                return False, "Volume too low"
            
            avg_volume = prev_20['volume'].mean()
            if avg_volume < 500000:
                return False, "Average volume too low"
            
            # Market cap estimation (rough)
            # We'll use price * average volume as a proxy for liquidity
            liquidity_proxy = latest['close'] * avg_volume
            if liquidity_proxy < 10000000:  
                return False, "Insufficient liquidity"
            
            return True, "Passed base filters"
            
        except Exception as e:
            return False, f"Error in filtering: {e}"

    def calculate_macd_suitability_score(self, data):
        """Calculate how suitable a stock is for MACD strategy"""
        if data is None or len(data) < 50:
            return 0
        
        try:
            score = 0
            latest = data.iloc[-1]
            prev_20 = data.iloc[-20:]
            
            # 1. MACD Signal Quality (30% weight)
            macd_signals = 0
            for i in range(len(prev_20) - 1):
                curr_hist = prev_20['Hist'].iloc[i+1]
                prev_hist = prev_20['Hist'].iloc[i]
                
                # Count MACD signal crossovers
                if (prev_hist <= 0 and curr_hist > 0) or (prev_hist >= 0 and curr_hist < 0):
                    macd_signals += 1
            
            # Optimal range: 2-4 signals in 20 days (not too choppy, not too flat)
            if 2 <= macd_signals <= 4:
                score += 30
            elif macd_signals == 1 or macd_signals == 5:
                score += 20
            else:
                score += 10
            
            # 2. Trend Strength (25% weight)
            price_change_20d = (latest['close'] - prev_20['close'].iloc[0]) / prev_20['close'].iloc[0]
            if abs(price_change_20d) > 0.05:  # At least 5% move in 20 days
                score += 25
            elif abs(price_change_20d) > 0.02:
                score += 15
            else:
                score += 5
            
            # 3. Volume Confirmation (20% weight)
            volume_trend = prev_20['volume'].corr(prev_20['close'])
            if abs(volume_trend) > 0.3:  # Volume follows price
                score += 20
            elif abs(volume_trend) > 0.1:
                score += 12
            else:
                score += 5
            
            # 4. Volatility Suitability (15% weight)
            if 'ATR' in data.columns:
                atr_pct = latest['ATR'] / latest['close']
                if 0.015 <= atr_pct <= 0.05:  # 1.5-5% daily range is ideal
                    score += 15
                elif 0.01 <= atr_pct <= 0.07:
                    score += 10
                else:
                    score += 3
            
            # 5. RSI Position (10% weight)
            if 'RSI' in data.columns and not pd.isna(latest['RSI']):
                rsi = latest['RSI']
                if 40 <= rsi <= 60:  # Neutral zone, room to move
                    score += 10
                elif 30 <= rsi <= 70:
                    score += 7
                else:
                    score += 2
            
            return min(score, 100)  # Cap at 100
            
        except Exception as e:
            logger.warning(f"Error calculating MACD suitability: {e}")
            return 0

    def screen_stocks_for_macd(self, timeframe='medium', max_stocks=10):
        """Main screening function for MACD strategy"""
        logger.info(f"Starting MACD stock screening for {timeframe} timeframe")
        
        stock_universe = self.get_stock_universe()
        candidates = []
        
        for i, symbol in enumerate(stock_universe):
            if i % 50 == 0:
                logger.info(f"Processed {i}/{len(stock_universe)} stocks")
            
            # Get data
            data = self.get_stock_data(symbol, days=100)
            if data is None:
                continue
            
            # Calculate indicators
            data = self.calculate_technical_indicators(data)
            if data is None:
                continue
            
            # Apply base filters
            passed, reason = self.apply_base_filters(symbol, data)
            if not passed:
                continue
            
            # Calculate MACD suitability score
            score = self.calculate_macd_suitability_score(data)
            
            if score > 50:  # Minimum threshold
                candidates.append({
                    'symbol': symbol,
                    'score': score,
                    'price': data['close'].iloc[-1],
                    'volume': data['volume'].iloc[-1],
                    'data_points': len(data)
                })
        
        # Sort by score and return top candidates
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Apply diversification (simple sector spreading)
        final_selection = self.diversify_selection(candidates[:max_stocks*2], max_stocks)
        
        logger.info(f"Selected {len(final_selection)} stocks for MACD strategy")
        for stock in final_selection:
            logger.info(f"  {stock['symbol']}: Score {stock['score']:.1f}")
        
        return final_selection

    def diversify_selection(self, candidates, max_stocks):
        """Simple diversification to avoid too many similar stocks"""
        # For now, just take top stocks with some spacing
        # In future, we can add sector classification
        selected = []
        used_first_letters = set()
        
        for candidate in candidates:
            if len(selected) >= max_stocks:
                break
            
            # Simple diversification: avoid too many stocks starting with same letter
            first_letter = candidate['symbol'][0]
            if first_letter not in used_first_letters or len(selected) < max_stocks // 2:
                selected.append(candidate)
                used_first_letters.add(first_letter)
        
        # Fill remaining slots if needed
        for candidate in candidates:
            if len(selected) >= max_stocks:
                break
            if candidate not in selected:
                selected.append(candidate)
        
        return selected[:max_stocks]

if __name__ == "__main__":
    screener = StockScreener()
    results = screener.screen_stocks_for_macd('medium', max_stocks=8)
    
    print("\nSelected stocks for MACD strategy:")
    for stock in results:
        print(f"{stock['symbol']}: Score {stock['score']:.1f}, Price ${stock['price']:.2f}")
