"""Tests for validate_trades() and calculate_pnl() in csv_analyzer."""
import pytest

from csv_analyzer import validate_trades, calculate_pnl


def _trade(date, symbol, action, price, shares):
    return {"date": date, "symbol": symbol, "action": action, "price": price, "shares": shares}


# ---------------------------------------------------------------------------
# validate_trades
# ---------------------------------------------------------------------------

class TestValidateTrades:

    def test_sell_lowercase_action_flagged(self):
        trades = [
            {"date": "2024-01-02", "symbol": "AAPL", "action": "sell", "price": 110.0, "shares": 10},
        ]
        warnings = validate_trades(trades)
        assert any(w["type"] == "unmatched_sell" and w["level"] == "warning" for w in warnings)

    def test_symbol_with_whitespace_still_matched(self):
        trades = [
            {"date": "2024-01-01", "symbol": "AAPL ", "action": "BUY", "price": 100.0, "shares": 10},
            {"date": "2024-01-02", "symbol": "AAPL", "action": "SELL", "price": 110.0, "shares": 10},
        ]
        warnings = validate_trades(trades)
        assert not any(w["type"] == "unmatched_sell" for w in warnings)

    def test_sell_missing_date_field(self):
        trades = [
            {"symbol": "AAPL", "action": "SELL", "price": 110.0, "shares": 10},
        ]
        warnings = validate_trades(trades)
        assert any(w["type"] == "unmatched_sell" and "unknown date" in w["message"] for w in warnings)

    def test_missing_level_key_defaults_to_warning(self):
        # Simulate a trade warning without a level key
        items = [
            {"type": "duplicate", "message": "dup"},
            {"type": "unmatched_sell", "message": "sell"},
        ]
        # Patch analyze_uploaded_trades to use these items
        from csv_analyzer import analyze_uploaded_trades
        def fake_validate_trades(_):
            return items
        import csv_analyzer
        orig = csv_analyzer.validate_trades
        csv_analyzer.validate_trades = fake_validate_trades
        try:
            result = analyze_uploaded_trades("date,symbol,action,price,shares\n")
            assert "notices" in result
            assert all(w["type"] in {"duplicate", "unmatched_sell"} for w in result["warnings"])
        finally:
            csv_analyzer.validate_trades = orig

    def test_analyze_uploaded_trades_returns_notices_key(self):
        from csv_analyzer import analyze_uploaded_trades
        csv = "date,symbol,action,price,shares\n2024-01-01,AAPL,BUY,100,10\n2024-02-01,AAPL,SELL,110,10\n"
        result = analyze_uploaded_trades(csv)
        assert "notices" in result
        assert isinstance(result["notices"], list)

    def test_no_open_positions_empty_notices(self):
        from csv_analyzer import analyze_uploaded_trades
        csv = "date,symbol,action,price,shares\n2024-01-01,AAPL,BUY,100,10\n2024-02-01,AAPL,SELL,110,10\n"
        result = analyze_uploaded_trades(csv)
        assert result["notices"] == []
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

    def test_unclosed_position_is_info_not_warning(self):
        trades = [_trade("2024-01-01", "AAPL", "BUY", 100.0, 10)]
        items = validate_trades(trades)
        unclosed = [i for i in items if i["type"] == "unclosed_position"]
        assert len(unclosed) == 1
        assert unclosed[0]["level"] == "info"

    def test_unclosed_position_warns(self):
        trades = [_trade("2024-01-01", "AAPL", "BUY", 100.0, 10)]
        warnings = validate_trades(trades)
        assert any(w["type"] == "unclosed_position" for w in warnings)

    def test_duplicate_has_warning_level(self):
        trade = _trade("2024-01-01", "AAPL", "BUY", 100.0, 10)
        items = validate_trades([trade, trade])
        duplicates = [i for i in items if i["type"] == "duplicate"]
        assert all(d["level"] == "warning" for d in duplicates)

    def test_unmatched_sell_has_warning_level(self):
        trades = [_trade("2024-01-01", "AAPL", "SELL", 110.0, 10)]
        items = validate_trades(trades)
        unmatched = [i for i in items if i["type"] == "unmatched_sell"]
        assert all(u["level"] == "warning" for u in unmatched)

    def test_open_position_message_is_informational(self):
        trades = [_trade("2024-01-15", "TSLA", "BUY", 200.0, 5)]
        items = validate_trades(trades)
        unclosed = [i for i in items if i["type"] == "unclosed_position"]
        assert len(unclosed) == 1
        assert "TSLA" in unclosed[0]["message"]
        assert "2024-01-15" in unclosed[0]["message"]

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

    def test_multiple_sells_no_buy_each_flagged(self):
        # Two SELLs for the same symbol with no BUY — both should be flagged
        trades = [
            _trade("2024-01-01", "AAPL", "SELL", 110.0, 10),
            _trade("2024-01-02", "AAPL", "SELL", 115.0, 10),
        ]
        warnings = validate_trades(trades)
        unmatched = [w for w in warnings if w["type"] == "unmatched_sell"]
        assert len(unmatched) == 2
        assert all(w["level"] == "warning" for w in unmatched)

    def test_more_sells_than_buys_extra_sell_flagged(self):
        # One BUY consumed by first SELL; second SELL has no BUY left
        trades = [
            _trade("2024-01-01", "AAPL", "BUY", 100.0, 10),
            _trade("2024-02-01", "AAPL", "SELL", 110.0, 10),
            _trade("2024-03-01", "AAPL", "SELL", 120.0, 10),
        ]
        warnings = validate_trades(trades)
        unmatched = [w for w in warnings if w["type"] == "unmatched_sell"]
        assert len(unmatched) == 1
        assert "2024-03-01" in unmatched[0]["message"]
        assert unmatched[0]["level"] == "warning"


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
