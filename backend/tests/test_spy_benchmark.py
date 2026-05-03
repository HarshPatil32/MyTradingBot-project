"""Tests for spy_benchmark.fetch_spy_benchmark."""

import numpy as np
import pandas as pd
import pytest
from datetime import datetime
from unittest.mock import patch

from spy_benchmark import fetch_spy_benchmark

_MOCK_YF = "spy_benchmark.yf.download"


def _make_spy_df(first: str, last: str, start_price: float = 400.0, end_price: float = 480.0) -> pd.DataFrame:
    """Return a minimal SPY DataFrame with business-day DatetimeIndex."""
    dates = pd.bdate_range(start=first, end=last)
    prices = np.linspace(start_price, end_price, len(dates))
    return pd.DataFrame({"Close": prices}, index=dates)


def _sample_trades():
    return [
        {"date": "2023-01-03", "symbol": "AAPL", "action": "BUY",  "price": 130.0, "shares": 10},
        {"date": "2023-06-15", "symbol": "AAPL", "action": "SELL", "price": 180.0, "shares": 10},
        {"date": "2023-12-15", "symbol": "MSFT", "action": "BUY",  "price": 370.0, "shares": 5},
    ]


class TestFetchSpyBenchmark:
    @patch(_MOCK_YF)
    def test_returns_expected_keys(self, mock_dl):
        mock_dl.return_value = _make_spy_df("2023-01-03", "2023-12-15")
        result = fetch_spy_benchmark(_sample_trades())
        assert result is not None
        assert set(result.keys()) == {"start_date", "end_date", "start_price", "end_price", "total_return_pct"}

    @patch(_MOCK_YF)
    def test_date_range_matches_trade_min_max(self, mock_dl):
        mock_dl.return_value = _make_spy_df("2023-01-03", "2023-12-15")
        result = fetch_spy_benchmark(_sample_trades())
        assert result["start_date"] == "2023-01-03"
        assert result["end_date"] == "2023-12-15"

    @patch(_MOCK_YF)
    def test_total_return_pct_is_correct(self, mock_dl):
        start_price, end_price = 400.0, 480.0
        mock_dl.return_value = _make_spy_df("2023-01-03", "2023-12-15", start_price=start_price, end_price=end_price)
        result = fetch_spy_benchmark(_sample_trades())
        # The production code lowercases columns in-place; compute expected from known inputs
        dates = pd.bdate_range(start="2023-01-03", end="2023-12-15")
        prices = np.linspace(start_price, end_price, len(dates))
        expected = round((prices[-1] - prices[0]) / prices[0] * 100, 4)
        assert result["total_return_pct"] == expected

    @patch(_MOCK_YF)
    def test_yfinance_called_with_fetch_end_one_day_after_last_trade(self, mock_dl):
        mock_dl.return_value = _make_spy_df("2023-01-03", "2023-12-15")
        fetch_spy_benchmark(_sample_trades())
        call_kwargs = mock_dl.call_args.kwargs
        assert call_kwargs["start"] == datetime(2023, 1, 3)
        # end should be one day after the last trade date (2023-12-16)
        assert call_kwargs["end"] == datetime(2023, 12, 16)

    def test_returns_none_for_empty_trades(self):
        result = fetch_spy_benchmark([])
        assert result is None

    def test_returns_none_for_trades_with_no_dates(self):
        trades = [{"symbol": "AAPL", "action": "BUY", "price": 100.0, "shares": 1}]
        result = fetch_spy_benchmark(trades)
        assert result is None

    @patch(_MOCK_YF)
    def test_returns_none_when_yfinance_returns_empty(self, mock_dl):
        mock_dl.return_value = pd.DataFrame()
        result = fetch_spy_benchmark(_sample_trades())
        assert result is None

    @patch(_MOCK_YF)
    def test_returns_none_when_yfinance_raises(self, mock_dl):
        mock_dl.side_effect = Exception("network error")
        result = fetch_spy_benchmark(_sample_trades())
        assert result is None

    @patch(_MOCK_YF)
    def test_single_trade_still_returns_result(self, mock_dl):
        mock_dl.return_value = _make_spy_df("2023-06-01", "2023-06-01", start_price=440.0, end_price=440.0)
        trades = [{"date": "2023-06-01", "symbol": "AAPL", "action": "BUY", "price": 180.0, "shares": 5}]
        result = fetch_spy_benchmark(trades)
        assert result is not None
        assert result["start_date"] == "2023-06-01"
        assert result["end_date"] == "2023-06-01"

    @patch(_MOCK_YF)
    def test_invalid_date_entries_are_skipped(self, mock_dl):
        mock_dl.return_value = _make_spy_df("2023-01-03", "2023-06-15")
        trades = [
            {"date": "bad-date", "symbol": "X", "action": "BUY", "price": 1.0, "shares": 1},
            {"date": "2023-01-03", "symbol": "X", "action": "BUY", "price": 1.0, "shares": 1},
            {"date": "2023-06-15", "symbol": "X", "action": "SELL", "price": 2.0, "shares": 1},
        ]
        result = fetch_spy_benchmark(trades)
        assert result is not None
        assert result["start_date"] == "2023-01-03"
        assert result["end_date"] == "2023-06-15"

    @patch(_MOCK_YF)
    def test_partial_yfinance_data_still_returns_result(self, mock_dl):
        # yfinance returns fewer rows than the full date range (e.g. data gap)
        mock_dl.return_value = _make_spy_df("2023-03-01", "2023-09-01")
        result = fetch_spy_benchmark(_sample_trades())
        # Should still succeed using whatever rows were returned
        assert result is not None
        assert result["start_date"] == "2023-01-03"
        assert result["end_date"] == "2023-12-15"
        assert isinstance(result["total_return_pct"], float)

    @patch(_MOCK_YF)
    def test_returns_none_when_start_price_is_zero(self, mock_dl):
        dates = pd.bdate_range(start="2023-01-03", end="2023-12-15")
        prices = [0.0] + [450.0] * (len(dates) - 1)
        mock_dl.return_value = pd.DataFrame({"Close": prices}, index=dates)
        result = fetch_spy_benchmark(_sample_trades())
        assert result is None
