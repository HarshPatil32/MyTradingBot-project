import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY_ID = os.getenv("API_KEY_ID")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")

url = "https://paper-api.alpaca.markets/v2/orders"

headers = {
    "APCA-API-KEY-ID": API_KEY_ID,
    "APCA-API-SECRET-KEY": API_SECRET_KEY
}

data = {
    "symbol": "AAPL",
    "qty": 1,
    "side": "buy",
    "type": "market",
    "time_in_force": "gtc"
}

response = requests.post(url, headers=headers, json=data)

print(response.json())