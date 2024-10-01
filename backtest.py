import zipline
from zipline.api import order, record, symbol, set_benchmark, schedule_function, date_rules, time_rules
from zipline.finance import commission, slippage
import pandas as pd
import talib
import matplotlib.pyplot as plt
from app import detect_trend



def initialize(context):
    context.assets = [symbol('AAPL'), symbol('NVDA')]
    context.short_window = 20
    context.long_window = 50
    context.invested = {asset: False for asset in context.assets}  # Track if already invested

    # Set the benchmark to S&P 500
    set_benchmark(symbol('SPY'))

    # Schedule the check_trend function to run daily at market close
    schedule_function(check_trend, date_rules.every_day(), time_rules.market_close())



