"""
Fetches SPY historical returns over the date range of uploaded trades for benchmarking.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_spy_benchmark(trades: list[dict]) -> dict | None:
    """Return SPY return data covering the date range of the given trades.

    Extracts the earliest and latest trade dates, fetches SPY adjusted close
    prices via yfinance, and returns a summary dict for benchmarking.
    Returns None if trades are empty or data is unavailable.
    """
    if not trades:
        return None

    dates = []
    for trade in trades:
        d = trade.get("date")
        if d:
            try:
                dates.append(datetime.strptime(d, "%Y-%m-%d"))
            except ValueError:
                pass

    if not dates:
        return None

    start = min(dates)
    end = max(dates)

    # yfinance end parameter is exclusive, so add one day to include the last trade date
    fetch_end = end + timedelta(days=1)

    try:
        data = yf.download("SPY", start=start, end=fetch_end, auto_adjust=True, progress=False)
        data.columns = data.columns.str.lower()
    except Exception as exc:
        logger.warning("SPY benchmark fetch failed: %s", exc)
        return None

    if data.empty:
        logger.warning("SPY benchmark: no data available for %s to %s", start.date(), end.date())
        return None

    data = data.sort_index()
    start_price = float(data["close"].iloc[0])
    end_price = float(data["close"].iloc[-1])

    if start_price == 0:
        logger.warning("SPY benchmark: start price is zero, cannot compute return")
        return None

    total_return_pct = round((end_price - start_price) / start_price * 100, 4)

    return {
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "start_price": round(start_price, 4),
        "end_price": round(end_price, 4),
        "total_return_pct": total_return_pct,
    }
