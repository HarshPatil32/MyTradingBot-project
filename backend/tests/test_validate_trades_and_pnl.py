"""Tests for validate_trades() and calculate_pnl() in csv_analyzer."""
import pytest

from csv_analyzer import validate_trades, calculate_pnl


def _trade(date, symbol, action, price, shares):
    return {"date": date, "symbol": symbol, "action": action, "price": price, "shares": shares}


# ---------------------------------------------------------------------------
# validate_trades
# ---------------------------------------------------------------------------

class TestValidateTrades:
    def test_no_warnings_for_clean_trades(self):
        trades = [
            _trade("2024-01-01", "AAPL", "BUY", 100.0, 10),
            _trade("2024-02-01", "AAPL", "SELL", 110.0, 10),
        ]
        assert validate_trades(trades) == []

    def test_duplicate_trade_warns(self):
        trade = _trade("2024-01-01", "AAPL", "BUY", 100.0, 10)
        warnings = validate_trades([trade, trade])
        assert any(w["type"] == "duplicate" for w in warnings)

    def test_unmatched_sell_warns(self):
        trades = [_trade("2024-01-01", "AAPL", "SELL", 110.0, 10)]
        warnings = validate_trades(trades)
        assert any(w["type"] == "unmatched_sell" for w in warnings)

    def test_unclosed_position_warns(self):
        trades = [_trade("2024-01-01", "AAPL", "BUY", 100.0, 10)]
        warnings = validate_trades(trades)
        assert any(w["type"] == "unclosed_position" for w in warnings)

    def test_multiple_symbols_paired_independently(self):
        trades = [
            _trade("2024-01-01", "AAPL", "BUY", 100.0, 10),
            _trade("2024-01-01", "MSFT", "BUY", 200.0, 5),
            _trade("2024-02-01", "AAPL", "SELL", 110.0, 10),
            _trade("2024-02-01", "MSFT", "SELL", 210.0, 5),
        ]
        assert validate_trades(trades) == []

    def test_sell_before_buy_for_same_symbol_warns(self):
        trades = [
            _trade("2024-01-01", "AAPL", "SELL", 110.0, 10),
            _trade("2024-02-01", "AAPL", "BUY", 100.0, 10),
        ]
        warnings = validate_trades(trades)
        assert any(w["type"] == "unmatched_sell" for w in warnings)
        # The buy that comes after has no sell, so also unclosed
        assert any(w["type"] == "unclosed_position" for w in warnings)

    def test_returns_list(self):
        assert isinstance(validate_trades([]), list)

    def test_mixed_case_actions_no_warnings(self):
        trades = [
            _trade("2024-01-01", "AAPL", "buy", 100.0, 10),
            _trade("2024-02-01", "AAPL", "Sell", 110.0, 10),
        ]
        assert validate_trades(trades) == []

    def test_mixed_case_duplicate_detected(self):
        trade = _trade("2024-01-01", "AAPL", "buy", 100.0, 10)
        same_uppercase = _trade("2024-01-01", "AAPL", "BUY", 100.0, 10)
        warnings = validate_trades([trade, same_uppercase])
        assert any(w["type"] == "duplicate" for w in warnings)


# ---------------------------------------------------------------------------
# calculate_pnl
# ---------------------------------------------------------------------------

class TestCalculatePnl:
    def test_single_profitable_trade(self):
        trades = [
            _trade("2024-01-01", "AAPL", "BUY", 100.0, 10),
            _trade("2024-02-01", "AAPL", "SELL", 110.0, 10),
        ]
        result = calculate_pnl(trades)
        assert result["total_pnl"] == 100.0  # (110-100)*10

    def test_single_losing_trade(self):
        trades = [
            _trade("2024-01-01", "AAPL", "BUY", 110.0, 10),
            _trade("2024-02-01", "AAPL", "SELL", 100.0, 10),
        ]
        result = calculate_pnl(trades)
        assert result["total_pnl"] == -100.0

    def test_trade_pnl_list_length(self):
        trades = [
            _trade("2024-01-01", "AAPL", "BUY", 100.0, 10),
            _trade("2024-02-01", "AAPL", "SELL", 110.0, 10),
        ]
        result = calculate_pnl(trades)
        assert len(result["trade_pnl"]) == 1

    def test_equity_curve_matches_trade_pnl_count(self):
        trades = [
            _trade("2024-01-01", "AAPL", "BUY", 100.0, 10),
            _trade("2024-02-01", "AAPL", "SELL", 110.0, 10),
        ]
        result = calculate_pnl(trades)
        assert len(result["equity_curve"]) == len(result["trade_pnl"])

    def test_total_return_pct_positive(self):
        trades = [
            _trade("2024-01-01", "AAPL", "BUY", 100.0, 10),
            _trade("2024-02-01", "AAPL", "SELL", 110.0, 10),
        ]
        result = calculate_pnl(trades)
        # P&L = 100, cost = 1000, return = 10%
        assert result["total_return_pct"] == 10.0

    def test_unmatched_sell_skipped(self):
        # A SELL with no prior BUY should not crash and should not appear in trade_pnl
        trades = [_trade("2024-01-01", "AAPL", "SELL", 110.0, 10)]
        result = calculate_pnl(trades)
        assert result["trade_pnl"] == []
        assert result["total_pnl"] == 0.0

    def test_empty_trades(self):
        result = calculate_pnl([])
        assert result["total_pnl"] == 0.0
        assert result["trade_pnl"] == []
        assert result["equity_curve"] == []
        assert result["total_return_pct"] == 0.0

    def test_fifo_pairing_multiple_buys(self):
        # Two buys at different prices; sells should match in FIFO order
        trades = [
            _trade("2024-01-01", "AAPL", "BUY", 100.0, 10),
            _trade("2024-01-15", "AAPL", "BUY", 120.0, 10),
            _trade("2024-02-01", "AAPL", "SELL", 130.0, 10),  # matches first BUY @ 100
        ]
        result = calculate_pnl(trades)
        assert result["trade_pnl"][0]["buy_price"] == 100.0
        assert result["trade_pnl"][0]["pnl"] == 300.0  # (130-100)*10

    def test_cumulative_pnl_accumulates(self):
        trades = [
            _trade("2024-01-01", "AAPL", "BUY", 100.0, 10),
            _trade("2024-02-01", "AAPL", "SELL", 110.0, 10),  # +100
            _trade("2024-03-01", "MSFT", "BUY", 200.0, 5),
            _trade("2024-04-01", "MSFT", "SELL", 220.0, 5),   # +100
        ]
        result = calculate_pnl(trades)
        assert result["total_pnl"] == 200.0
        assert result["equity_curve"][-1]["cumulative_pnl"] == 200.0

    def test_result_keys_present(self):
        result = calculate_pnl([])
        assert set(result.keys()) == {"trade_pnl", "equity_curve", "total_pnl", "total_return_pct"}

    def test_mixed_case_actions_compute_correctly(self):
        trades = [
            _trade("2024-01-01", "AAPL", "buy", 100.0, 10),
            _trade("2024-02-01", "AAPL", "Sell", 110.0, 10),
        ]
        result = calculate_pnl(trades)
        assert result["total_pnl"] == 100.0
        assert len(result["trade_pnl"]) == 1

    def test_mixed_case_sell_actions_no_warnings(self):
        trades = [
            _trade("2024-01-01", "AAPL", "BUY", 100.0, 10),
            _trade("2024-02-01", "AAPL", "sell", 110.0, 10),
        ]
        assert validate_trades(trades) == []

    def test_mixed_case_sell_duplicate_detected(self):
        trade = _trade("2024-01-01", "AAPL", "SELL", 100.0, 10)
        same_lowercase = _trade("2024-01-01", "AAPL", "sell", 100.0, 10)
        warnings = validate_trades([trade, same_lowercase])
        assert any(w["type"] == "duplicate" for w in warnings)

    def test_missing_action_does_not_crash(self):
        trades = [
            {"date": "2024-01-01", "symbol": "AAPL", "price": 100.0, "shares": 10},
            _trade("2024-02-01", "AAPL", "SELL", 110.0, 10),
        ]
        # Should not raise, should treat missing action as non-BUY/SELL and skip
        warnings = validate_trades(trades)
        assert isinstance(warnings, list)

    def test_null_action_does_not_crash(self):
        trades = [
            {"date": "2024-01-01", "symbol": "AAPL", "action": None, "price": 100.0, "shares": 10},
            _trade("2024-02-01", "AAPL", "SELL", 110.0, 10),
        ]
        warnings = validate_trades(trades)
        assert isinstance(warnings, list)

    def test_mixed_case_sell_actions_compute_correctly(self):
        trades = [
            _trade("2024-01-01", "AAPL", "BUY", 100.0, 10),
            _trade("2024-02-01", "AAPL", "sell", 110.0, 10),
        ]
        result = calculate_pnl(trades)
        assert result["total_pnl"] == 100.0
        assert len(result["trade_pnl"]) == 1

    def test_missing_action_skipped_in_pnl(self):
        trades = [
            {"date": "2024-01-01", "symbol": "AAPL", "price": 100.0, "shares": 10},
            _trade("2024-02-01", "AAPL", "SELL", 110.0, 10),
        ]
        result = calculate_pnl(trades)
        assert result["total_pnl"] == 0.0
        assert result["trade_pnl"] == []

    def test_null_action_skipped_in_pnl(self):
        trades = [
            {"date": "2024-01-01", "symbol": "AAPL", "action": None, "price": 100.0, "shares": 10},
            _trade("2024-02-01", "AAPL", "SELL", 110.0, 10),
        ]
        result = calculate_pnl(trades)
        assert result["total_pnl"] == 0.0
        assert result["trade_pnl"] == []
