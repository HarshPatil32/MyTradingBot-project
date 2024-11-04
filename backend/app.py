from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from threading import Thread, Event
import logging
from symbols import symbol
from moving_averages import run_monitoring, backtest_strategy_crossover
from datetime import datetime
from test_against_SP import get_spy_investment
from RSI_trading import backtest_strategy_RSI
from MACD_trading import backtest_strategy_MACD

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

@app.route('/RSI-strategy', methods=['GET'])
def rsi_strategy():
    stocks = request.args.get('stocks')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    initial_balance = request.args.get('initial_balance', default=100000, type=int)  
    
    stock_list = stocks.split(',') if stocks else []
    start_date_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
    str = backtest_strategy_RSI(stock_list, start_date_dt, end_date_dt, initial_balance)

    formatted_result = str.replace("\n", "<br />")
    return jsonify(formatted_result)

@app.route('/MACD-strategy', methods=['GET'])
def MACD_strategy():
    stocks = request.args.get('stocks')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    initial_balance = request.args.get('initial_balance', default=100000, type=int)  
    
    stock_list = stocks.split(',') if stocks else []
    start_date_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
    str = backtest_strategy_MACD(stock_list, start_date_dt, end_date_dt, initial_balance)

    formatted_result = str.replace("\n", "<br />")
    return jsonify(formatted_result)


@app.route('/spy-investment', methods=['GET'])
def spy_investment():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    initial_balance = request.args.get('initial_balance', default=100000, type=int)  

    try:
        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)
    except (ValueError, TypeError) as e:
        return jsonify({"error": "Invalid input. Please provide 'start_date' and 'end_date' in ISO format."}), 400

    final_balance = get_spy_investment(start_date, end_date, initial_balance)

    return jsonify({"final_balance": final_balance})  




    

    

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
    symbols = ["SPY", "PG"]  

    print(backtest_strategy_MACD(symbols, start_date, end_date))

    # app.run()



