# MyTrading-Bot-project
Trading Bot with frontend and backend

Backend: Utilized python-flask as well as alpaca api in order for trading
- Alpaca with api key and secret key connects to my paper trading account and allows me to test the algorithm in live time
- Backtesting route will allow you to choose any two dates to test the algorithm between, currently beats the S&P
- Uses talib for financial indicators
- Alpaca stock data does not go farther back than 2016 so that is a handicap as of now but beats S&P all other years

Frontend: Utilizes React.js for basic isualizations of data
- Stock by stock growth patters based on chosen strategy
- Comparison to S&P 500 to show profitability

STRATEGIES
Moving averages:
- Very basic, checks where moving averages cross with long being 200 days and short being 50 days
- Buy signal (golden cross): short MA crosses above long MA
- Sell signal (death cross): short MA crosses below long MA
- Stop loss of 0.05 of investment

More testing strategies to be added
