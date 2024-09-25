import requests
import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
import talib
from datetime import datetime

load_dotenv()

API_KEY_ID = os.getenv("API_KEY_ID")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")

url = "https://paper-api.alpaca.markets/v2"

THRESHOLD = 170




HEADERS = {
    "APCA-API-KEY-ID": API_KEY_ID,
    "APCA-API-SECRET-KEY": API_SECRET_KEY
}

def get_current_price(symbol):
    url = f"{url}/stocls/{symbol}/quote"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return float(data["last"]["price"])

def place_order(symbol, qty, side):
    url = f"{url}/orders"
    order_data = {
        "symbol": symbol,
        "qty": 1,
        "side": "buy",
        "type": "market",
        "time_in_force": "gtc"
    }
    response = requests.post(url, headers=HEADERS, json=order_data)
    return response.json()