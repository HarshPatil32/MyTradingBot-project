from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from threading import Thread, Event
import logging
from symbols import symbol
from moving_averages import run_monitoring, backtest_strategy_crossover
from datetime import datetime


app = Flask(__name__)

CORS(app)




@app.route("/webhookcallback", methods=["POST"])
def hook():
    if request.is_json:
        data = request.get_json()
        print(data)
        return jsonify({"status": "success", "message": "Webhook received"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid content type"}), 400
    

@app.route("/moving-averages", methods = ["GET"])
def get_moving_average_data():
    stocks = request.args.get('stocks')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    stock_list = stocks.split(',') if stocks else []
    start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
    str = backtest_strategy_crossover(stock_list, start_date_dt, end_date_dt)

    formatted_result = str.replace("\n", "<br />")
    return jsonify(formatted_result)


    

    

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

    start_date = datetime(2019, 1, 1)  
    end_date = datetime(2024, 1, 1)
    symbols = ["uyvufyi"]  

    print(backtest_strategy_crossover(symbols, start_date, end_date))

    # app.run()



