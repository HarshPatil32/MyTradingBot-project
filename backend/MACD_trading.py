import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta
from alpaca_trade_api import TimeFrame
import pandas as pd
import numpy as np
import time

# Try to import TA-Lib, fall back to pandas implementation if not available
try:
    import talib
    TALIB_AVAILABLE = True
    print("✅ TA-Lib imported successfully")
except ImportError:
    TALIB_AVAILABLE = False
    print("⚠️ TA-Lib not available, using pandas implementation")

load_dotenv()

API_KEY_ID = os.getenv("API_KEY_ID")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")

url = "https://paper-api.alpaca.markets"




api = tradeapi.REST(API_KEY_ID, API_SECRET_KEY, url)

def get_market_regime_data(start_date, end_date):
    try:
        extended_start = start_date - timedelta(days=250)
        
        # Get SPY data
        spy_data = api.get_bars(
            'SPY', 
            TimeFrame.Day,
            start=extended_start.isoformat() + 'Z',
            end=end_date.isoformat() + 'Z'
        ).df
        
        spy_data['ma_50'] = spy_data['close'].rolling(window=50).mean()
        spy_data['ma_200'] = spy_data['close'].rolling(window=200).mean()
        spy_data['ma_20'] = spy_data['close'].rolling(window=20).mean()
        spy_data['high_20'] = spy_data['close'].rolling(window=20).max()
        spy_data['drawdown_from_high'] = (spy_data['close'] / spy_data['high_20']) - 1
        
        # Get VIX data
        try:
            vix_data = api.get_bars(
                'VIX', 
                TimeFrame.Day,
                start=extended_start.isoformat() + 'Z',
                end=end_date.isoformat() + 'Z'
            ).df
        except:
            # If VIX not available create synthetic volatility from SPY (ideally don't want this but good for production)
            print("VIX data not available, using SPY volatility as proxy")
            spy_data['returns'] = spy_data['close'].pct_change()
            spy_data['volatility'] = spy_data['returns'].rolling(window=20).std() * np.sqrt(252) * 100
            spy_data['vix_proxy'] = spy_data['volatility'].clip(lower=10, upper=80)
            vix_data = pd.DataFrame({'close': spy_data['vix_proxy']}, index=spy_data.index)
        
        return spy_data, vix_data
        
    except Exception as e:
        print(f"Error fetching market regime data: {e}")
        return None, None

def check_market_regime(spy_data, vix_data, current_date, vix_threshold=30, crash_threshold=-0.10, use_regime_filter=True):
    if not use_regime_filter:
        return {
            'can_trade': True,
            'regime': 'filter_disabled',
            'reason': 'Market regime filter is disabled'
        }
    
    if spy_data is None or vix_data is None:
        print("Market regime data unavailable, allowing trade by default")
        return {
            'can_trade': True,
            'regime': 'unknown',
            'reason': 'Market data unavailable'
        }
    
    try:
        spy_row = spy_data.loc[spy_data.index <= current_date].iloc[-1]
        try:
            vix_row = vix_data.loc[vix_data.index <= current_date].iloc[-1]
            current_vix = vix_row['close']
        except:
            if 'vix_proxy' in spy_data.columns:
                current_vix = spy_row['vix_proxy']
            else:
                current_vix = 20 
        
        current_price = spy_row['close']
        ma_50 = spy_row['ma_50']
        ma_200 = spy_row['ma_200']
        drawdown = spy_row['drawdown_from_high']
        
        conditions = {
            'vix_ok': current_vix < vix_threshold,
            'above_ma200': current_price > ma_200,
            'above_ma50': current_price > ma_50,
            'no_crash': drawdown > crash_threshold,
            'golden_cross': ma_50 > ma_200  # 50-day MA above 200-day MA
        }
        
        if not conditions['vix_ok']:
            return {
                'can_trade': False,
                'regime': 'high_volatility',
                'reason': f"VIX too high: {current_vix:.1f} (threshold: {vix_threshold})",
                'vix': current_vix,
                'spy_vs_ma200': 'above' if conditions['above_ma200'] else 'below'
            }
        
        if not conditions['no_crash']:
            return {
                'can_trade': False,
                'regime': 'market_crash',
                'reason': f"Market down {drawdown*100:.1f}% from recent high",
                'vix': current_vix,
                'drawdown': drawdown
            }
        
        if not conditions['above_ma200']:
            return {
                'can_trade': False,
                'regime': 'bear_market',
                'reason': f"SPY below 200-day MA (bearish)",
                'vix': current_vix,
                'spy_vs_ma200': 'below'
            }
        
        regime_quality = sum(conditions.values())
        
        if regime_quality >= 4:
            regime_label = 'bull_strong'
            confidence = 'high'
        elif regime_quality >= 3:
            regime_label = 'bull_moderate'
            confidence = 'medium'
        else:
            regime_label = 'bull_weak'
            confidence = 'low'
        
        return {
            'can_trade': True,
            'regime': regime_label,
            'reason': f"Favorable market conditions ({confidence} confidence)",
            'vix': current_vix,
            'spy_vs_ma200': 'above',
            'golden_cross': conditions['golden_cross'],
            'confidence': confidence
        }
        
    except Exception as e:
        print(f"Error checking market regime: {e}")
        return {
            'can_trade': True,
            'regime': 'error',
            'reason': f'Error checking regime: {e}'
        }

def calculate_indicators(data, fastperiod, slowperiod, signalperiod):
    """
    Calculate MACD indicators using TA-Lib if available, otherwise use pandas
    """
    if TALIB_AVAILABLE:
        # Use TA-Lib (preferred method)
        data['MACD'], data['Signal'], data['Hist'] = talib.MACD(
            data['close'], 
            fastperiod=fastperiod, 
            slowperiod=slowperiod, 
            signalperiod=signalperiod
        )
    else:
        # Use pandas implementation as fallback
        # Calculate EMAs
        ema_fast = data['close'].ewm(span=fastperiod).mean()
        ema_slow = data['close'].ewm(span=slowperiod).mean()
        
        # Calculate MACD line
        data['MACD'] = ema_fast - ema_slow
        
        # Calculate Signal line (EMA of MACD)
        data['Signal'] = data['MACD'].ewm(span=signalperiod).mean()
        
        # Calculate Histogram
        data['Hist'] = data['MACD'] - data['Signal']
    
    return data

def backtest_strategy_MACD(symbols, start_date, end_date, initial_balance=100000, trailing_stop_loss=0.15, fastperiod=12, slowperiod=26, signalperiod=9, return_monthly_data=False, use_regime_filter=True, vix_threshold=30):
    portfolio_balance = initial_balance
    total_trade_history = []
    return_str = ''
    monthly_performance = [] if return_monthly_data else None
    
    spy_data, vix_data = get_market_regime_data(start_date, end_date)
    
    if use_regime_filter and spy_data is not None:
        print(f"Market regime filter ENABLED (VIX threshold: {vix_threshold})")
    else:
        print(f"Market regime filter DISABLED or data unavailable")
    
    regime_stats = {
        'total_days': 0,
        'trading_days': 0,
        'paused_days': 0,
        'regime_blocks': []  # To see when trading is paused
    }

    for symbol in symbols:
        
        data = api.get_bars(
            symbol, TimeFrame.Day,
            start=start_date.isoformat() + 'Z',
            end=end_date.isoformat() + 'Z'
        ).df

        try:
            data = calculate_indicators(data, fastperiod, slowperiod, signalperiod)
        except KeyError:
            return f"{symbol} is not the name of a real stock"
        
        position = 0
        balance = portfolio_balance / len(symbols)
        trade_history = []
        purchase_price = None
        highest_price = None
        
        for index in range(1, len(data)):
            current_date = data.index[index]
            regime_stats['total_days'] += 1
            
            regime_info = check_market_regime(
                spy_data, vix_data, current_date, 
                vix_threshold=vix_threshold,
                use_regime_filter=use_regime_filter
            )
            
            can_trade = regime_info['can_trade']
            
            if not can_trade:
                regime_stats['paused_days'] += 1
                if position > 0 and regime_info['regime'] in ['high_volatility', 'market_crash']:
                    price = data['close'].iloc[index]
                    balance += position * price
                    trade_history.append({
                        'symbol': symbol,
                        'action': 'sell',
                        'price': price,
                        'qty': position,
                        'date': current_date,
                        'reason': f"regime_exit: {regime_info['reason']}"
                    })
                    position = 0
                    purchase_price = None
                    highest_price = None
                continue
            
            regime_stats['trading_days'] += 1
            
            macd_line = data['MACD'].iloc[index]
            signal_line = data['Signal'].iloc[index]
            price = data['close'].iloc[index]

            if macd_line > signal_line and data['Hist'].iloc[index] > 0 and position == 0:
                qty = int(balance/price)
                if qty > 0:  
                    balance -= qty * price
                    position = qty
                    purchase_price = price
                    highest_price = price
                    trade_history.append({
                        'symbol': symbol,
                        'action': 'buy',
                        'price': price,
                        'qty': qty,
                        'date': current_date,
                        'regime': regime_info['regime'],
                        'vix': regime_info.get('vix', 'N/A')
                    })

            if position > 0:
                highest_price = max(highest_price, price)

            if position > 0 and (macd_line < signal_line or price <= highest_price * (1 - trailing_stop_loss)):
                balance += position * price
                sell_reason = 'macd_signal' if macd_line < signal_line else 'trailing_stop'
                trade_history.append({
                    'symbol': symbol,
                    'action': 'sell',
                    'price': price,
                    'qty': position,
                    'date': current_date,
                    'reason': sell_reason,
                    'regime': regime_info['regime']
                })
                position = 0
                purchase_price = None
                highest_price = None

        if position > 0:
            balance += position * data['close'].iloc[-1]
            trade_history.append({
                'symbol': symbol,
                'action': 'sell',
                'price': data['close'].iloc[-1],
                'qty': position,
                'date': data.index[-1],
                'reason': 'backtest_end'
            })

        portfolio_balance += balance - (initial_balance / len(symbols))
        total_trade_history.extend(trade_history)

        return_str += (
            f"Initial Balance: ${initial_balance / len(symbols):,.2f}, "
            f"Final Balance for {symbol}: ${balance:,.2f}\n"
        )

    return_str += (
        f"Portfolio Initial Balance: ${initial_balance:,.2f}, "
        f"Final Portfolio Balance: ${portfolio_balance:,.2f}\n"
    )
    
    return return_str, portfolio_balance

def generate_monthly_performance(symbols, start_date, end_date, initial_balance=100000, fastperiod=12, slowperiod=26, signalperiod=9):
    """
    Generate monthly performance data for MACD strategy to use in frontend charts
    """
    from datetime import datetime, timedelta
    import pandas as pd
    
    # Get the optimized backtest results
    _, final_balance = backtest_strategy_MACD(
        symbols, start_date, end_date, initial_balance, 
        fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod
    )
    
    # Calculate number of months between start and end date
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if months <= 0:
        months = 1
    
    # Calculate monthly growth rate
    total_return = (final_balance - initial_balance) / initial_balance
    monthly_return = (1 + total_return) ** (1/months) - 1
    
    # Generate monthly data points
    monthly_data = []
    current_balance = initial_balance
    current_date = start_date
    
    for month in range(months + 1):
        if month == 0:
            monthly_data.append({
                'month': 'Start',
                'balance': initial_balance,
                'date': current_date.strftime('%Y-%m')
            })
        elif month == months:
            # Use actual final balance for last month
            monthly_data.append({
                'month': f'Month {month}',
                'balance': final_balance,
                'date': current_date.strftime('%Y-%m')
            })
        else:
            # Use calculated monthly growth
            current_balance *= (1 + monthly_return)
            monthly_data.append({
                'month': f'Month {month}',
                'balance': round(current_balance, 2),
                'date': current_date.strftime('%Y-%m')
            })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return monthly_data




