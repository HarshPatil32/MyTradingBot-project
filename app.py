from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
import talib
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.requests import MarketOrderRequest, OrderSide, OrderType
import numpy as np
from flask_socketio import SocketIO
from threading import Thread, Event
import time

app = Flask(__name__)




load_dotenv()

API_KEY_ID = os.getenv("API_KEY_ID")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")

url = "https://paper-api.alpaca.markets"




api = tradeapi.REST(API_KEY_ID, API_SECRET_KEY, url)

short_window = 20
long_window = 50

def get_historical_data(symbol):
    barset = api.get_bars(
        symbol, TimeFrame.Minute, start = (datetime.now() - timedelta(days=1)).isoformat(),
        end = datetime.now().isoformat()
    ).df

    symbol_data = barset[barset['symbol'] == symbol]
    
    return symbol_data

def calculate_moving_averages(symbol):
    data = get_historical_data(symbol)

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


