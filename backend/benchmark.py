"""
Fetches historical returns for a given ticker over the date range of uploaded trades.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import yfinance as yf

logger = logging.getLogger(__name__)

# Simple in-process cache: (ticker, start_str, end_str) -> result dict or None
_cache: dict[tuple[str, str, str], dict | None] = {}

# Minimum number of trading day rows required for a meaningful return
MIN_TRADING_DAYS = 2


def fetch_benchmark(trades: list[dict], ticker: str) -> dict | None:
    """Return return data for the given ticker covering the date range of the given trades.

    Extracts the earliest and latest trade dates, fetches adjusted close prices
    via yfinance, and returns a summary dict for benchmarking.
    Returns None if trades are empty, data is unavailable, or the period is too short.
    """
    if not trades:
        return None

    if not ticker or not ticker.strip():
        logger.warning("fetch_benchmark called with empty ticker")
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

    cache_key = (ticker, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    if cache_key in _cache:
        return _cache[cache_key]

    # yfinance end parameter is exclusive, so add one day to include the last trade date
    fetch_end = end + timedelta(days=1)

    try:
        data = yf.download(ticker, start=start, end=fetch_end, auto_adjust=True, progress=False)
        data.columns = data.columns.str.lower()
    except Exception as exc:
        logger.warning("%s benchmark fetch failed: %s", ticker, exc)
        _cache[cache_key] = None
        return None

    if data.empty:
        logger.warning("%s benchmark: no data available for %s to %s", ticker, start.date(), end.date())
        _cache[cache_key] = None
        return None

    data = data.sort_index()

    if len(data) < MIN_TRADING_DAYS:
        logger.warning(
            "%s benchmark: only %d trading day(s) of data for %s to %s — period too short",
            ticker, len(data), start.date(), end.date(),
        )
        _cache[cache_key] = None
        return None

    start_price = float(data["close"].iloc[0])
    end_price = float(data["close"].iloc[-1])

    if start_price == 0:
        logger.warning("%s benchmark: start price is zero, cannot compute return", ticker)
        _cache[cache_key] = None
        return None

    total_return_pct = round((end_price - start_price) / start_price * 100, 4)

    # Actual trading day dates yfinance used (may differ from trade dates if
    # the trade date fell on a weekend or holiday)
    actual_start_date = data.index[0].strftime("%Y-%m-%d")
    actual_end_date = data.index[-1].strftime("%Y-%m-%d")

    result = {
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "actual_start_date": actual_start_date,
        "actual_end_date": actual_end_date,
        "start_price": round(start_price, 4),
        "end_price": round(end_price, 4),
        "total_return_pct": total_return_pct,
    }
    _cache[cache_key] = result
    return result
