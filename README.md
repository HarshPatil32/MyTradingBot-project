# MyTrading-Bot-project
Trading Bot with frontend and backend

Backend: Utilized python-flask as well as alpaca api in order for trading
- Alpaca with api key and secret key connects to my paper trading account and allows me to test the algorithm in live time
- Backtesting route will allow you to choose any two dates to test the algorithm between, currently beats the S & P

Frontend: Utilizes React.js for basic isualizations of data
- Stock by stock growth patters based on chosen strategy
- Comparison to S&P 500 to show profitability

STRATEGIES
Moving averages:
- Very basic, checks where moving averages cross with long being 200 days and short being 50 days
- Buy signal (golden cross): short MA crosses above long MA
- Sell signal (death cross): short MA crosses below long MA
- Stop loss of 0.05 of investment
