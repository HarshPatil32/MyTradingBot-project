from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
import logging
import os
from datetime import datetime
from test_against_SP import get_spy_investment, generate_spy_monthly_performance
from MACD_trading import backtest_strategy_MACD, generate_monthly_performance
from optimize_MACD import optimize_macd_parameters

app = Flask(__name__)

# Configure CORS properly - allow all origins for now (you can restrict this later)
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins for deployment
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False  # Set to False when allowing all origins
    }
})

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "API is running", "message": "Flask trading API"}), 200

@app.route("/webhookcallback", methods=["POST"])
def hook():
    try:
        if request.is_json:
            data = request.get_json()
            logger.info(f"Webhook received: {data}")
            return jsonify({"status": "success", "message": "Webhook received"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid content type"}), 400
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/MACD-strategy', methods=['GET'])
def MACD_strategy():
    try:
        stocks = request.args.get('stocks')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        initial_balance = request.args.get('initial_balance', default=100000, type=int)
        optimize = request.args.get('optimize', default='true').lower() == 'true'
        
        # Validate required parameters
        if not stocks or not start_date_str or not end_date_str:
            return jsonify({"error": "Missing required parameters: stocks, start_date, end_date"}), 400

        stock_list = [stock.strip() for stock in stocks.split(',') if stock.strip()]
        
        try:
            start_date_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError as e:
            return jsonify({"error": f"Invalid date format. Use YYYY-MM-DD: {str(e)}"}), 400

        logger.info(f"Processing MACD strategy for stocks: {stock_list}, dates: {start_date_str} to {end_date_str}, optimize: {optimize}")
        
        if optimize:
            # First optimize parameters for the given stocks and dates
            optimization_result = optimize_macd_parameters(
                symbols=stock_list,
                start_date=start_date_dt,
                end_date=end_date_dt,
                initial_balance=initial_balance,
                n_iterations=15  # Reduced for faster response time
            )
            
            optimized_params = optimization_result['optimized_params']
            
            # Run backtest with optimized parameters
            str_result, final_balance = backtest_strategy_MACD(
                stock_list, 
                start_date_dt, 
                end_date_dt, 
                initial_balance,
                fastperiod=optimized_params['fastperiod'],
                slowperiod=optimized_params['slowperiod'],
                signalperiod=optimized_params['signalperiod']
            )
            
            formatted_result = str_result.replace("\n", "<br />")
            
            # Generate monthly performance data for charting
            monthly_data = generate_monthly_performance(
                stock_list,
                start_date_dt,
                end_date_dt,
                initial_balance,
                fastperiod=optimized_params['fastperiod'],
                slowperiod=optimized_params['slowperiod'],
                signalperiod=optimized_params['signalperiod']
            )
            
            # Return both the backtest result and optimized parameters
            return jsonify({
                "backtest_result": formatted_result,
                "optimized_parameters": optimized_params,
                "optimization_performance": {
                    "best_balance": optimization_result['best_balance'],
                    "total_return": optimization_result['total_return']
                },
                "monthly_performance": monthly_data
            }), 200
        else:
            # Run backtest with default parameters (legacy behavior)
            str_result, _ = backtest_strategy_MACD(stock_list, start_date_dt, end_date_dt, initial_balance)
            formatted_result = str_result.replace("\n", "<br />")
            return jsonify({"backtest_result": formatted_result}), 200
            
    except Exception as e:
        logger.error(f"MACD strategy error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/spy-investment', methods=['GET'])
def spy_investment():
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        initial_balance = request.args.get('initial_balance', default=100000, type=int)

        # Validate required parameters
        if not start_date_str or not end_date_str:
            return jsonify({"error": "Missing required parameters: start_date, end_date"}), 400

        try:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        except (ValueError, TypeError) as e:
            return jsonify({"error": "Invalid date format. Please provide dates in ISO format (YYYY-MM-DD)."}), 400

        logger.info(f"Processing SPY investment for dates: {start_date_str} to {end_date_str}")
        
        final_balance = get_spy_investment(start_date, end_date, initial_balance)
        monthly_data = generate_spy_monthly_performance(start_date, end_date, initial_balance)
        
        return jsonify({
            "final_balance": final_balance,
            "monthly_performance": monthly_data
        }), 200
        
    except Exception as e:
        logger.error(f"SPY investment error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get port from environment variable (Render provides this) or default to 5001
    port = int(os.environ.get('PORT', 5001))
    
    # Run the app on all interfaces for Render deployment
    app.run(host='0.0.0.0', port=port, debug=False)