import logging
import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
import talib
import time



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  
        logging.StreamHandler()          
    ])




load_dotenv()

API_KEY_ID = os.getenv("API_KEY_ID")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")

url = "https://paper-api.alpaca.markets"





api = tradeapi.REST(API_KEY_ID, API_SECRET_KEY, url)

short_window = 50
long_window = 200

def send_trend_signal_to_webhook(trend, symbol):
    url = "http://localhost:5000/webhookcallback"
    payload = {
        "symbol": symbol,
        "trend": trend
    }
    response = requests.post(url, json = payload)
    return response.status_code, response.json()


def get_historical_data(symbol):
    barset = api.get_bars(
        symbol, TimeFrame.Day, start = (datetime.now() - timedelta(days=1)).isoformat() + 'Z',
        end = datetime.now().isoformat() + 'Z'
    ).df

    
    return barset

def calculate_indicators(data):
    data['short_ma'] = talib.EMA(data['close'], timeperiod=short_window)
    data['long_ma'] = talib.EMA(data['close'], timeperiod=long_window)
    data['RSI'] = talib.RSI(data['close'], timeperiod=14)
    data['ADX'] = talib.ADX(data['high'], data['low'], data['close'], timeperiod=14)
    data['ATR'] = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
    return data


    return data

def get_slope(time_period, periods=3):
    if len(time_period) < periods:
        logging.warning(f"Not enough data to calculate slope. Required: {periods}, Available: {len(time_period)}")
        return None  
    return time_period.iloc[-1] - time_period.iloc[-periods]


def detect_crossover(data):
    short_ma = data['short_ma'].iloc[-1]
    long_ma = data['long_ma'].iloc[-1]
    prev_short_ma = data['short_ma'].iloc[-2]
    prev_long_ma = data['long_ma'].iloc[-2]

    # Buy signal (golden cross): short MA crosses above long MA
    if prev_short_ma <= prev_long_ma and short_ma > long_ma:
        return "buy"

    # Sell signal (death cross): short MA crosses below long MA
    elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
        return "sell"

    return "hold"

    
def monitor_stock(symbol):
    data = get_historical_data(symbol.name)
    MA = calculate_moving_averages(data)
    # RSI = MA['RSI'].iloc[-1]
    # logging.info(f"The RSI for {symbol.name} is {RSI}")
    old_trend = symbol.trend
    trend = detect_trend(MA)
    if old_trend != trend:
        symbol.trend = trend
        if trend == 'upward' and old_trend == 'sideways':
            market_buy(symbol.name, 20)
            logging.info(f"You just bought 20 shares of {symbol.name}")
        elif trend == 'sideways' and old_trend == 'upward':
            market_sell(symbol.name, 20)
            logging.info(f"You just sold 20 shares of {symbol.name}")
        elif trend == 'sideways' and old_trend == 'downward':
            market_buy(symbol.name, 20)
            logging.info(f"You just bought 20 shares of {symbol.name}")
        elif trend == 'downward' and old_trend == 'sideways':
            market_sell(symbol.name, 20)
            logging.info(f"You just sold 20 shares of {symbol.name}")
        elif trend == 'upward' and old_trend == 'downward':
            market_buy(symbol.name, 40)
            logging.info(f"You just closed short position and bought 20 shares of {symbol.name}")
        elif trend == 'downward' and old_trend == 'upward':
            market_sell(symbol.name, 40)
            logging.info(f"You just closed long position and sold 20 shares of {symbol.name}")

    
    

def run_monitoring(symbols, interval=30):
    while True:
        for symbol in symbols:
            monitor_stock(symbol)
        time.sleep(interval)

def market_buy(symbol, price, balance, risk_per_trade=0.01):
    risk_amount = balance * risk_per_trade
    qty = risk_amount / price  
    try:
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side='buy',
            type='market',
            time_in_force='gtc'
        )
        return order
    except Exception as e:
        logging.error(f"Error placing buy order for {symbol}: {e}")

def market_sell(symbol, qty, stop_loss=None, take_profit=None):
    try:
        price = api.get_last_trade(symbol).price
        if stop_loss and price <= stop_loss:
            logging.info(f"Selling {symbol} due to stop loss at {price}")
        elif take_profit and price >= take_profit:
            logging.info(f"Selling {symbol} to take profit at {price}")
        else:
            logging.info(f"Selling {symbol} at market price")
        
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side='sell',
            type='market',
            time_in_force='gtc'
        )
        return order
    except Exception as e:
        logging.error(f"Error placing sell order for {symbol}: {e}")


def backtest_strategy_crossover(symbol, start_date, end_date, initial_balance=100000):
    logging.info(f"Backtesting {symbol} from {start_date} to {end_date}")
    
    data = api.get_bars(
        symbol, TimeFrame.Minute, 
        start=start_date.isoformat() + 'Z', 
        end=end_date.isoformat() + 'Z'
    ).df
    
    data = calculate_indicators(data)
    
    position = 0  
    balance = initial_balance  
    trade_history = []  

    for index in range(1, len(data)):  
        trend_signal = detect_crossover(data.iloc[:index + 1])
        price = data['close'].iloc[index]
        
        if trend_signal == "buy" and position == 0:
            qty = int(balance * 0.1 / price)  
            balance -= qty * price  
            position = qty
            logging.info(f"Bought {qty} shares at {price} on {data.index[index]}")
            trade_history.append({
                'action': 'buy',
                'price': price,
                'qty': qty,
                'date': data.index[index]
            })
        
        elif trend_signal == "sell" and position > 0:
            balance += position * price  
            logging.info(f"Sold {position} shares at {price} on {data.index[index]}")
            trade_history.append({
                'action': 'sell',
                'price': price,
                'qty': position,
                'date': data.index[index]
            })
            position = 0  

   
    if position > 0:
        balance += position * data['close'].iloc[-1]

    logging.info(f"Initial Balance: {initial_balance}, Final Balance: {balance}")
    
    return balance, trade_history
