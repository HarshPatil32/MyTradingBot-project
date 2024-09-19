from flask import Flask, request, jsonify

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


if __name__ == "__main__":
    app.run()