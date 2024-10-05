from flask import Flask, request, jsonify
from dotenv import load_dotenv
from threading import Thread, Event
import logging
from symbols import symbol
from moving_averages import run_monitoring, backtest_strategy
from datetime import datetime


app = Flask(__name__)




@app.route("/webhookcallback", methods=["POST"])
def hook():
    if request.is_json:
        data = request.get_json()
        print(data)
        return jsonify({"status": "success", "message": "Webhook received"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid content type"}), 400
    

    

if __name__ == "__main__":
    '''
    apple = symbol("AAPL")
    spy = symbol("SPY")
    nvidia = symbol("NVDA")
    salesforce = symbol("CRM")
    coke = symbol("KO")
    jnj = symbol("JNJ")
    amazon = symbol("AMZN")
    lockheed = symbol("LMT")
    pandg = symbol ("PG")
    general_electric = symbol ("GE")
    microsoft = symbol ("MSFT")
    jpm = symbol("JPM")
    duke_energy = symbol("DUK")
    alcon = symbol("ALC")
    symbols = [apple, spy, nvidia, salesforce, coke, jnj, amazon, lockheed, pandg, general_electric, microsoft, jpm, duke_energy, alcon]
    logging.info("Beginning Thread")
    monitor_thread = Thread(target=run_monitoring, args=(symbols,))
    monitor_thread.start()
    
    app.run()
    '''

    start_date = datetime(2023, 1, 1)  
    end_date = datetime(2023, 9, 30)
    symbol = "NVDA"  

    backtest_strategy(symbol, start_date, end_date)



