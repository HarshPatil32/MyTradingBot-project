from flask import Flask, request, jsonify
from dotenv import load_dotenv
from threading import Thread, Event
import logging
from symbols import symbol
from moving_averages import run_monitoring

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
    apple = symbol("AAPL")
    spy = symbol("SPY")
    nvidia = symbol("NVDA")
    salesforce = symbol("CRM")
    coke = symbol("KO")
    jnj = symbol("JNJ")
    amazon = symbol("AMZN")
    lockheed = symbol("LMT")
    symbols = [apple, spy, nvidia, salesforce, coke, jnj, amazon, lockheed]
    logging.info("Beginning Thread")
    monitor_thread = Thread(target=run_monitoring, args=(symbols,))
    monitor_thread.start()
    
    app.run()



