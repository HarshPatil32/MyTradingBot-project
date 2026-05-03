"""Tests for benchmark.fetch_benchmark."""

import numpy as np
import pandas as pd
import pytest
from datetime import datetime
from unittest.mock import patch

from benchmark import fetch_benchmark

_MOCK_YF = "benchmark.yf.download"


def _make_df(first: str, last: str, start_price: float, end_price: float) -> pd.DataFrame:
    """Return a minimal price DataFrame with business-day DatetimeIndex."""
    dates = pd.bdate_range(start=first, end=last)
    prices = np.linspace(start_price, end_price, len(dates))
    return pd.DataFrame({"Close": prices}, index=dates)


def _sample_trades():
    return [
        {"date": "2023-01-03", "symbol": "AAPL", "action": "BUY",  "price": 130.0, "shares": 10},
        {"date": "2023-06-15", "symbol": "AAPL", "action": "SELL", "price": 180.0, "shares": 10},
        {"date": "2023-12-15", "symbol": "MSFT", "action": "BUY",  "price": 370.0, "shares": 5},
    ]


class TestFetchBenchmark:
    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    @patch(_MOCK_YF)
    def test_returns_expected_keys(self, mock_dl, ticker):
        mock_dl.return_value = _make_df("2023-01-03", "2023-12-15", 400.0, 480.0)
        result = fetch_benchmark(_sample_trades(), ticker)
        assert result is not None
        assert set(result.keys()) == {"start_date", "end_date", "start_price", "end_price", "total_return_pct"}

    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    @patch(_MOCK_YF)
    def test_date_range_matches_trade_min_max(self, mock_dl, ticker):
        mock_dl.return_value = _make_df("2023-01-03", "2023-12-15", 400.0, 480.0)
        result = fetch_benchmark(_sample_trades(), ticker)
        assert result["start_date"] == "2023-01-03"
        assert result["end_date"] == "2023-12-15"

    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    @patch(_MOCK_YF)
    def test_total_return_pct_is_correct(self, mock_dl, ticker):
        start_price, end_price = 400.0, 480.0
        mock_dl.return_value = _make_df("2023-01-03", "2023-12-15", start_price, end_price)
        result = fetch_benchmark(_sample_trades(), ticker)
        dates = pd.bdate_range(start="2023-01-03", end="2023-12-15")
        prices = np.linspace(start_price, end_price, len(dates))
        expected = round((prices[-1] - prices[0]) / prices[0] * 100, 4)
        assert result["total_return_pct"] == expected

    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    @patch(_MOCK_YF)
    def test_yfinance_called_with_correct_ticker_and_dates(self, mock_dl, ticker):
        mock_dl.return_value = _make_df("2023-01-03", "2023-12-15", 400.0, 480.0)
        fetch_benchmark(_sample_trades(), ticker)
        call_args = mock_dl.call_args
        assert call_args.args[0] == ticker
        assert call_args.kwargs["start"] == datetime(2023, 1, 3)
        # end should be one day after the last trade date (2023-12-16)
        assert call_args.kwargs["end"] == datetime(2023, 12, 16)

    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    def test_returns_none_for_empty_trades(self, ticker):
        result = fetch_benchmark([], ticker)
        assert result is None

    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    def test_returns_none_for_trades_with_no_dates(self, ticker):
        trades = [{"symbol": "AAPL", "action": "BUY", "price": 100.0, "shares": 1}]
        result = fetch_benchmark(trades, ticker)
        assert result is None

    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    @patch(_MOCK_YF)
    def test_returns_none_when_yfinance_returns_empty(self, mock_dl, ticker):
        mock_dl.return_value = pd.DataFrame()
        result = fetch_benchmark(_sample_trades(), ticker)
        assert result is None

    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    @patch(_MOCK_YF)
    def test_returns_none_when_yfinance_raises(self, mock_dl, ticker):
        mock_dl.side_effect = Exception("network error")
        result = fetch_benchmark(_sample_trades(), ticker)
        assert result is None

    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    @patch(_MOCK_YF)
    def test_single_trade_still_returns_result(self, mock_dl, ticker):
        mock_dl.return_value = _make_df("2023-06-01", "2023-06-01", 440.0, 440.0)
        trades = [{"date": "2023-06-01", "symbol": "AAPL", "action": "BUY", "price": 180.0, "shares": 5}]
        result = fetch_benchmark(trades, ticker)
        assert result is not None
        assert result["start_date"] == "2023-06-01"
        assert result["end_date"] == "2023-06-01"

    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    @patch(_MOCK_YF)
    def test_invalid_date_entries_are_skipped(self, mock_dl, ticker):
        mock_dl.return_value = _make_df("2023-01-03", "2023-06-15", 400.0, 450.0)
        trades = [
            {"date": "bad-date", "symbol": "X", "action": "BUY", "price": 1.0, "shares": 1},
            {"date": "2023-01-03", "symbol": "X", "action": "BUY", "price": 1.0, "shares": 1},
            {"date": "2023-06-15", "symbol": "X", "action": "SELL", "price": 2.0, "shares": 1},
        ]
        result = fetch_benchmark(trades, ticker)
        assert result is not None
        assert result["start_date"] == "2023-01-03"
        assert result["end_date"] == "2023-06-15"

    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    @patch(_MOCK_YF)
    def test_partial_yfinance_data_still_returns_result(self, mock_dl, ticker):
        mock_dl.return_value = _make_df("2023-03-01", "2023-09-01", 400.0, 450.0)
        result = fetch_benchmark(_sample_trades(), ticker)
        assert result is not None
        assert result["start_date"] == "2023-01-03"
        assert result["end_date"] == "2023-12-15"
        assert isinstance(result["total_return_pct"], float)

    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    @patch(_MOCK_YF)
    def test_returns_none_when_start_price_is_zero(self, mock_dl, ticker):
        dates = pd.bdate_range(start="2023-01-03", end="2023-12-15")
        prices = [0.0] + [450.0] * (len(dates) - 1)
        mock_dl.return_value = pd.DataFrame({"Close": prices}, index=dates)
        result = fetch_benchmark(_sample_trades(), ticker)
        assert result is None

    @pytest.mark.parametrize("bad_ticker", ["", "   "])
    def test_empty_ticker_returns_none(self, bad_ticker):
        result = fetch_benchmark(_sample_trades(), bad_ticker)
        assert result is None

    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    @patch(_MOCK_YF)
    def test_ticker_passed_through_to_yfinance(self, mock_dl, ticker):
        mock_dl.return_value = _make_df("2023-01-03", "2023-12-15", 400.0, 480.0)
        fetch_benchmark(_sample_trades(), ticker)
        assert mock_dl.call_args.args[0] == ticker
