from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
import talib
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
from threading import Thread, Event
import time
import zipline
from zipline.api import order, record, symbol, set_benchmark, schedule_function, date_rules, time_rules
from zipline.finance import commission, slippage
import matplotlib.pyplot as plt
import logging

app = Flask(__name__)

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
    data = get_historical_data(symbol)
    MA = calculate_moving_averages(data)

    trend = detect_trend(MA)
    logging.info(f"The current trend for {symbol} is {trend}")

def run_monitoring(symbol, interval=60):
    while True:
        monitor_stock(symbol)
        time.sleep(interval)

@app.route("/webhookcallback", methods=["POST"])
def hook():
    if request.is_json:
        data = request.get_json()
        print(data)
        return jsonify({"status": "success", "message": "Webhook received"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid content type"}), 400
    

if __name__ == "__main__":
    # Start the stock monitoring thread for a specific stock symbol, e.g., AAPL
    symbol = "AAPL"
    logging.info("Beginning Thread")
    monitor_thread = Thread(target=run_monitoring, args=(symbol,))
    monitor_thread.start()
    
    app.run()



