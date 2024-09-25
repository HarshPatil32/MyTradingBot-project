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

app = Flask(__name__)




load_dotenv()

API_KEY_ID = os.getenv("API_KEY_ID")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")

url = "https://paper-api.alpaca.markets/v2"




HEADERS = {
    "APCA-API-KEY-ID": API_KEY_ID,
    "APCA-API-SECRET-KEY": API_SECRET_KEY
}

short_window = 20
long_window = 50

def get_historical_data(symbol, timeframe, limit):
    api_url = f"{url}/stocks/{symbol}/bars"
    params = {
        "timeframe": timeframe,
        "limit": limit
    }
    response = requests.get(api_url, headers = HEADERS, params = params)
    data = response.json()
    return [bar['close'] for bar in data['bars']]

def calcualte_moving_averages(symbol):
    historical_prices = get_historical_data(symbol, "1Min", 50)
    prices = np.array(historical_prices)
    short_ma = talib.SMA(prices, timeperiod=short_window)
    long_ma = talib.SMA(prices, timeperiod=long_window)

    return short_ma[-1], long_ma[-1]



def get_current_price(symbol):
    url = f"{url}/stocls/{symbol}/quote"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return float(data["last"]["price"])

def place_order(symbol, qty, side):
    url = f"{url}/orders"
    order_data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": "market",
        "time_in_force": "gtc"
    }
    response = requests.post(url, headers=HEADERS, json=order_data)
    return response.json()

@app.route("/webhookcallback", methods=["POST"])
def hook():
    if request.is_json:
        data = request.get_json()  # Parse the JSON payload
        print(data)
        # Perform any additional processing here
        return jsonify({"status": "success", "message": "Webhook received"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid content type"}), 400
    



if __name__ == "__main__":
    app.run()