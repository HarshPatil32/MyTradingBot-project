from flask import Flask, request, jsonify
from send_request import get_current_price, THRESHOLD, place_order
app = Flask(__name__)

@app.route("/webhookcallback", methods=["POST"])
def hook():
    if request.is_json:
        data = request.get_json()  # Parse the JSON payload
        print(data)
        # Perform any additional processing here
        return jsonify({"status": "success", "message": "Webhook received"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid content type"}), 400
    

@app.route("/buy_if_dips", methods=["GET"])
def buy_if_dips():
    current_price = get_current_price("AAPL")
    if current_price < THRESHOLD:
        # If price dips below threshold, buy AAPL
        order = place_order("AAPL", 1, "buy")
        return jsonify({"message": "Bought 1 share of AAPL", "order": order}), 200
    else:
        return jsonify({"message": f"Current price is {current_price}, above threshold"}), 200



if __name__ == "__main__":
    app.run()