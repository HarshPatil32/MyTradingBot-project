import logging
import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta
from alpaca_trade_api import TimeFrame
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

short_window = 3
long_window = 15

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
    # data['RSI'] = talib.RSI(data['close'], timeperiod=14)
    # data['ADX'] = talib.ADX(data['high'], data['low'], data['close'], timeperiod=14)
   # data['ATR'] = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
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

    if prev_short_ma <= prev_long_ma and short_ma > long_ma:
        return "buy"

    elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
        return "sell"

    return "hold"

    
def monitor_stock(symbol):
    data = get_historical_data(symbol.name)
    data = calculate_indicators(data)
    new_trend = detect_crossover(data)
    old_trend = symbol.trend
    
    if old_trend != new_trend:
        symbol.trend = new_trend
        
        if new_trend == "buy" and old_trend != "buy":
            market_buy(symbol.name, data['close'].iloc[-1], 20) 
            logging.info(f"Bought 20 shares of {symbol.name} at {data['close'].iloc[-1]}")
        
        elif new_trend == "sell" and old_trend != "sell":
            market_sell(symbol.name, 20) 
            logging.info(f"Sold 20 shares of {symbol.name} at {data['close'].iloc[-1]}")

    
    

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

def market_sell(symbol, qty):
    try:
        price = api.get_last_trade(symbol).price
        
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


def backtest_strategy_crossover(symbols, start_date, end_date, initial_balance=100000, stop_loss = 0.01):
    logging.info(f"Backtesting portfolio from {start_date} to {end_date}")
    logging.info(f'here are the symbols, {symbols}')
    
    portfolio_balance = initial_balance
    total_trade_history = []
    return_str = ''

    for symbol in symbols:
        logging.info(f"Backtesting {symbol} from {start_date} to {end_date}")
        
        data = api.get_bars(
            symbol, TimeFrame.Day, 
            start=start_date.isoformat() + 'Z', 
            end=end_date.isoformat() + 'Z'
        ).df
        
        try:
            data = calculate_indicators(data)
        except KeyError:
            return f"{symbol} is not the name of a real stock"
        
        position = 0  
        balance = portfolio_balance / len(symbols)  
        trade_history = []  
        purchase_price = None 

        for index in range(1, len(data)):
            trend_signal = detect_crossover(data.iloc[:index + 1])
            price = data['close'].iloc[index]

            if position > 0 and price <= purchase_price * (1 - stop_loss):
                balance += position * price
                # logging.info(f"Stop-loss triggered for {symbol}, sold {position} shares at {price} on {data.index[index]}")
                trade_history.append({
                    'symbol': symbol,
                    'action': 'sell',
                    'price': price,
                    'qty': position,
                    'date': data.index[index],
                    'reason': 'stop_loss'
                })
                position = 0
                purchase_price = None
            elif trend_signal == "buy" and position == 0:
                qty = int(balance / price)  
                balance -= qty * price
                position = qty
                purchase_price = price
                # logging.info(f"Bought {qty} shares of {symbol} at {price} on {data.index[index]}")
                trade_history.append({
                    'symbol': symbol,
                    'action': 'buy',
                    'price': price,
                    'qty': qty,
                    'date': data.index[index]
                })
            
            elif trend_signal == "sell" and position > 0:
                balance += position * price
                # logging.info(f"Sold {position} shares of {symbol} at {price} on {data.index[index]}")
                trade_history.append({
                    'symbol': symbol,
                    'action': 'sell',
                    'price': price,
                    'qty': position,
                    'date': data.index[index]
                })
                position = 0
                purchase_price = None

        if position > 0:
            balance += position * data['close'].iloc[-1]

        portfolio_balance += balance - (initial_balance / len(symbols))
        total_trade_history.extend(trade_history)

        # logging.info(f"Initial Balance: {initial_balance / len(symbols)}, Final Balance for {symbol}: {balance}")
        return_str+=(f"Initial Balance: {initial_balance / len(symbols)}, Final Balance for {symbol}: {balance}\n")

    # logging.info(f"Portfolio Initial Balance: {initial_balance}, Final Portfolio Balance: {portfolio_balance}")
    return_str+=(f"Portfolio Initial Balance: {initial_balance}, Final Portfolio Balance: {portfolio_balance}\n")
    
    return return_str

