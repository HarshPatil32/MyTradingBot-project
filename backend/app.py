from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
import logging
import os
from datetime import datetime
import requests
import json
import numpy as np

# Try to import trading modules with error handling
try:
    from test_against_SP import get_spy_investment, generate_spy_monthly_performance
    from MACD_trading import backtest_strategy_MACD, generate_monthly_performance
    from optimize_MACD import optimize_macd_parameters
    TRADING_MODULES_AVAILABLE = True
except ImportError as e:
    logging.error(f"Trading modules not available: {e}")
    TRADING_MODULES_AVAILABLE = False

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

@app.route("/heartbeat", methods=["GET"])
def heartbeat():
    """Lightweight heartbeat endpoint to keep server alive"""
    return jsonify({
        "status": "alive", 
        "timestamp": datetime.now().isoformat(),
        "message": "Server is running"
    }), 200


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
    if not TRADING_MODULES_AVAILABLE:
        return jsonify({"error": "Trading modules not available. Please check server setup."}), 500
    
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
    if not TRADING_MODULES_AVAILABLE:
        return jsonify({"error": "Trading modules not available. Please check server setup."}), 500
        
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

def generate_selection_reason(score):
    """Give a reason for why it chose the stock"""
    if score >= 85:
        return "Excellent MACD signals with strong momentum"
    elif score >= 75:
        return "Strong MACD patterns and good volume"
    elif score >= 65:
        return "Good technical setup for MACD strategy"
    elif score >= 55:
        return "Decent MACD potential with acceptable risk"
    else:
        return "Basic MACD suitability"


@app.route('/get-optimal-stocks', methods=['GET'])
def get_optimal_stocks():
    """This route will select the most optimal stocks for you"""
    if not TRADING_MODULES_AVAILABLE:
        return jsonify({"error": "Trading modules not available. Please check server setup"}), 500
    
    try:
        from stock_screener import StockScreener

        # Get the parameters we need
        timeframe = request.args.get('timeframe', default = 'medium')
        max_stocks = request.args.get('max_stocks', default=5, type=int)
        strategy_mode = request.args.get('strategy_mode', default = 'moderate')

        # Check the timeframe
        valid_timeframes = ['short', 'medium', 'long']
        if timeframe not in valid_timeframes:
            return jsonify({"error": "The timeframe isn't valid, please choose short, medium or long"}), 400
        
        # Cap the max stocks at 10
        if max_stocks < 1 or max_stocks > 10:
            return jsonify({"error": "Please choose a number between 1 and 10 inclusive"})
        
        screener = StockScreener()
        selected_stocks = screener.screen_stocks_for_macd(timeframe=timeframe, max_stocks=max_stocks)

        if not selected_stocks:
            return jsonify({"error": "No suitable stocks found with your criteria",
                            "fallback_stocks": ["AAPL", "MSFT", "GOOGL", "TSLA"]}), 200
        
        # DEBUG: Test 1 - Can we serialize the raw selected_stocks?
        print("DEBUG: Testing raw selected_stocks serialization...")
        try:
            import json
            json.dumps(selected_stocks)
            print("DEBUG: Raw selected_stocks - OK")
        except Exception as e:
            print(f"DEBUG: Raw selected_stocks FAILED: {e}")
        
        # stock reasoning
        for stock in selected_stocks:
            stock['reason'] = generate_selection_reason(stock['score'])
            
        # DEBUG: Test 2 - Can we serialize after adding reasons?
        print("DEBUG: Testing selected_stocks with reasons...")
        try:
            json.dumps(selected_stocks)
            print("DEBUG: Selected_stocks with reasons - OK")
        except Exception as e:
            print(f"DEBUG: Selected_stocks with reasons FAILED: {e}")

        response_data = {
            "selected_stocks": selected_stocks,
            "timeframe": timeframe,
            "strategy_mode": strategy_mode,
            "total_candidates_screened": int(len(selected_stocks) * 10),  # Rough estimate
            "selection_criteria": f"MACD-optimized for {timeframe}-term trading",
            "timestamp": datetime.now().isoformat()
        }
        
        # DEBUG: Test 3 - Can we serialize the full response_data?
        print("DEBUG: Testing full response_data...")
        try:
            json.dumps(response_data)
            print("DEBUG: Full response_data - OK")
        except Exception as e:
            print(f"DEBUG: Full response_data FAILED: {e}")
            
        # DEBUG: Test 4 - Let's check individual fields
        print("DEBUG: Checking individual response fields...")
        for key, value in response_data.items():
            try:
                json.dumps({key: value})
                print(f"DEBUG: {key} - OK")
            except Exception as e:
                print(f"DEBUG: {key} FAILED: {e}")
                print(f"DEBUG: {key} type: {type(value)}")
                if key == "selected_stocks" and isinstance(value, list):
                    for i, stock in enumerate(value):
                        try:
                            json.dumps(stock)
                            print(f"DEBUG: stock[{i}] ({stock.get('symbol', 'unknown')}) - OK")
                        except Exception as stock_e:
                            print(f"DEBUG: stock[{i}] ({stock.get('symbol', 'unknown')}) FAILED: {stock_e}")
                            for stock_key, stock_value in stock.items():
                                print(f"DEBUG:   {stock_key}: {type(stock_value)} = {stock_value}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Stock screening error: {str(e)}")
        return jsonify({
            "error": f"Stock screening failed: {str(e)}",
            "fallback_stocks": ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA", "SPY"]
        }), 500

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get port from environment variable (Render provides this) or default to 5001
    port = int(os.environ.get('PORT', 5001))
    
    # Run the app on all interfaces for Render deployment
    app.run(host='0.0.0.0', port=port, debug=False)