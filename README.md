# MyTrading-Bot-project

HOW TO RUN:
- Set up frontend with 'npm run dev'
- Set up backend with 'flask run'
- Choose which strategy, frontend doesn't look pretty but only used to visualize gains/losses

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

BEST STOCKS FOR MACD STRAT:
- Mid cap
- Avg volume > 500k
    - Sufficient liquidity and limits slippage
- Beta > 1.5
- Price performance (month up)
    - Not necessary just helps
- Price above SMA50
    - Also not necessary but I found it helps
- Relative volume > 1.5
I used Finwiz as stock screener

Using the requirements above I chose the symbols ADT (ADT Inc), ALHC (Alignment Healthcare Inc), EPR (EPR Properties), SKT (Tanger Inc), not because these were the best I just used the filter and chose 4 random from the results to ensure fair distribution.

The backend will split the 'initial investment' you entered equally among each stock.

Click calculate SPY Investment to see what you would have gained if you put the same amount of money in SPY over the time period you chose.
Fetch data will tell you how much you gained per stock and in total over that time period.

With these symbols
- Outperformed S&P 500 by +9.93% over 3 years (Jan 1 2022 - Jan 1 2025)
- Generated +32.62% total returns on chosen stocks (ADT, ALHC, EPR, SKT)



OTHER STRATEGIES
Moving averages:
- Very basic, checks where moving averages cross with long being 15 days and short being 3 days
- Buy signal (golden cross): short MA crosses above long MA
- Sell signal (death cross): short MA crosses below long MA
- Stop loss of 0.01 of investment

RSI:
- Sells if hits trailing stop loss or RSI exceeds 70
- Buys if RSI < 30
- Definitely safe strategy and can give positive gains, but not as optimal as other strategies


