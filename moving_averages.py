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
        logging.FileHandler("app.log"),  # Logs to app.log file
        logging.StreamHandler()          # Logs to console/terminal
    ])




load_dotenv()

API_KEY_ID = os.getenv("API_KEY_ID")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")

url = "https://paper-api.alpaca.markets"





api = tradeapi.REST(API_KEY_ID, API_SECRET_KEY, url)

short_window = 20
long_window = 50

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
        symbol, TimeFrame.Minute, start = (datetime.now() - timedelta(days=1)).isoformat() + 'Z',
        end = datetime.now().isoformat() + 'Z'
    ).df

    
    return barset

def calculate_moving_averages(data):

    data['short_ma'] = talib.SMA(data['close'], timeperiod = short_window)
    data['long_ma'] = talib.SMA(data['close'], timeperiod = long_window)

    return data

def get_slope(time_period, periods = 3):
    return time_period.iloc[-1] - time_period.iloc[-periods]


def detect_trend(data):
    short_slope = get_slope(data['short_ma'])
    long_slope = get_slope(data['long_ma'])

    if short_slope > 0 and long_slope > 0 and data['short_ma'].iloc[-1] > data['long_ma'].iloc[-1]:
        return "upward"
    elif short_slope < 0 and long_slope < 0 and data['short_ma'].iloc[-1] < data['long_ma'].iloc[-1]:
        return "downward"
    elif abs(short_slope) < 0.1 and abs(long_slope) < 0.1:  # Adjust the threshold for your needs
        return "sideways"
    else:
        return "indecisive"
    
def monitor_stock(symbol):
    data = get_historical_data(symbol.name)
    MA = calculate_moving_averages(data)

    old_trend = symbol.trend
    trend = detect_trend(MA)
    if symbol.trend != trend:
        symbol.trend = trend
        if trend == 'upward' and (old_trend == 'downard' or old_trend == 'sideways'):
            market_buy(symbol.name, 5)
            logging.info(f"You just bought 5 shares of {symbol}")
        elif trend == 'sideways' and old_trend == 'upward':
            market_sell(symbol.name, 5)
            logging.info(f"You just sold 5 shares of {symbol}")
        elif trend == 'sideways' and old_trend == 'downward':
            market_buy(symbol.name, 5)
            logging.info(f"You just bought 5 shares of {symbol}")
        elif trend == 'downward' and (old_trend == 'upward' or old_trend == 'sideways'):
            market_sell(symbol.name, 5)
            logging.info(f"You just sold 5 shares of {symbol}")
        elif trend == 'upward' and old_trend == 'downward':
            market_sell(symbol.name, 10)
            logging.info(f"You just closed long position and sold 5 shares of {symbol}")
        elif trend == 'downward' and old_trend == 'upward':
            market_buy(symbol.name, 10)
            logging.info(f"You just closed short position and bought 5 shares of {symbol}")

    
    
    logging.info(f"The current trend for {symbol} is {trend}")

def run_monitoring(symbols, interval=60):
    while True:
        for symbol in symbols:
            monitor_stock(symbol)
        time.sleep(interval)

def market_buy(symbol, qty):
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
        logging.info(f"error placing order {e}")

def market_sell(symbol, qty):
    try:
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side='sell',
            type='market',
            time_in_force='gtc'
        )
        return order
    except Exception as e:
        logging.info(f"error placing order {e}")