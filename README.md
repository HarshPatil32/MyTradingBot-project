# MyTrading-Bot-project
Trading Bot with frontend and backend

Backend: Utilized python-flask as well as alpaca api in order for trading
- Alpaca with api key and secret key connects to my paper trading account and allows me to test the algorithm in live time
- Backtesting route will allow you to choose any two dates to test the algorithm between, currently beats the S&P based on which
securities you choose
- Uses talib for financial indicators
- Alpaca stock data does not go farther back than 2016 so that is a handicap as of now

Frontend: Utilizes React.js for basic isualizations of data
- Stock by stock growth patters based on chosen strategy
- Comparison to S&P 500 to show profitability

STRATEGIES
Moving averages:
- Very basic, checks where moving averages cross with long being 15 days and short being 3 days
- Buy signal (golden cross): short MA crosses above long MA
- Sell signal (death cross): short MA crosses below long MA
- Stop loss of 0.01 of investment

RSI:
- Sells if hits trailing stop loss or RSI exceeds 70
- Buys if RSI < 30
- Definitely safe strategy and can give positive gains, but not as optimal as other strategies

MACD Divergence:
- Checks when price of an asset and the MACD indicator are moving in opposite directions
- MACD line: calculates by subtracting 26-period EMA from the 12-period EMA
- Signal line: 9-period EMA of the MACD line itself
- If market is showing lower lows and MACD shows higher lows, signs of bullish divergence and vice versa
- Trailing stop loss of 0.05 (can be less since MACD line reacts quicker)
- So far tends to beat the market
- Since this is the most promising algorithm as of now, added Bayesian optimization to find best parameters for fast period
slow period and signal period
- Gives about 5-15% extra returns than original parameters
- Takes some extra time:
    - Uses backtest_strategy_MACD as objective function
    - Re-training Gaussian process
    - 100 random points for acquisition optmization
    - Runs 25 iterations with each of the above
- Overall time tradeoffs are worth the gains as it is a few extra seconds



More testing strategies to be added
