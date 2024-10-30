from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from flask import Flask, request, jsonify
from alpaca.data.timeframe import TimeFrame
import os

load_dotenv()

API_KEY_ID = os.getenv("API_KEY_ID")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")

url = "https://paper-api.alpaca.markets"





api = tradeapi.REST(API_KEY_ID, API_SECRET_KEY, url)

def get_spy_investment(start_date, end_date, initial_balance=100000):
    """Calculates the final balance of an initial investment in SPY from start_date to end_date."""
    
    data = api.get_bars(
        'SPY', TimeFrame.Day, 
        start=start_date.isoformat() + 'Z', 
        end=end_date.isoformat() + 'Z'
    ).df
    
    if data.empty:
        return "No data available for SPY in the specified date range.", 400

    initial_price = data['close'].iloc[0]
    final_price = data['close'].iloc[-1]
    
    final_balance = initial_balance * (final_price / initial_price)
    return final_balance