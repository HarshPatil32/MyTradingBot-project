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


load_dotenv()

API_KEY_ID = os.getenv("API_KEY_ID")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")

url = "https://paper-api.alpaca.markets"





api = tradeapi.REST(API_KEY_ID, API_SECRET_KEY, url)


def get_historical_data(symbol):
    barset = api.get_bars(
        symbol, TimeFrame.Day, start = (datetime.now() - timedelta(days=1)).isoformat() + 'Z',
        end = datetime.now().isoformat() + 'Z'
    ).df

    
    return barset

def calculate_indicators(data):
    data['RSI'] = talib.RSI(data['close'], timeperiod=14)
    return data

def backtest_strategy_RSI(symbols, start_date, end_date, initial_balance=100000, trailing_stop_loss = 0.05):
    portfolio_balance = initial_balance
    total_trade_history = []
    return_str = ''

    for symbol in symbols:
        
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
        highest_price = None

        for index in range(1, len(data)):
            RSI = data['RSI'].iloc[index]
            price = data['close'].iloc[index]

            if RSI < 30 and position == 0:
                qty = int(balance / price)  
                balance -= qty * price
                position = qty
                purchase_price = price
                highest_price = price
                trade_history.append({
                    'symbol': symbol,
                    'action': 'buy',
                    'price': price,
                    'qty': qty,
                    'date': data.index[index]
                })

            if position > 0:
                highest_price = max (highest_price, price)

            
            if position > 0 and (RSI >70 or price <= highest_price * (1 - trailing_stop_loss)):
                balance += position * price
                trade_history.append({
                    'symbol': symbol,
                    'action': 'sell',
                    'price': price,
                    'qty': position,
                    'date': data.index[index],
                    'reason': 'trailing_stop_loss'
                })
                position = 0
                purchase_price = None
                highest_price = None

        if position > 0:
            balance += position * data['close'].iloc[-1]

        portfolio_balance += balance - (initial_balance / len(symbols))
        total_trade_history.extend(trade_history)

        # logging.info(f"Initial Balance: {initial_balance / len(symbols)}, Final Balance for {symbol}: {balance}")
        return_str+=(f"Initial Balance: {initial_balance / len(symbols)}, Final Balance for {symbol}: {balance}\n")

    # logging.info(f"Portfolio Initial Balance: {initial_balance}, Final Portfolio Balance: {portfolio_balance}")
    return_str+=(f"Portfolio Initial Balance: {initial_balance}, Final Portfolio Balance: {portfolio_balance}\n")
    
    return return_str