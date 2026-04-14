"""Smoke tests for the three analysis modules with minimum viable input."""
import pytest

from statistical_tests import run_significance_tests
from overfitting_detector import detect_overfitting
from transaction_costs import calculate_real_costs
# Fixtures

ONE_TRADE_PNL = [5.0]
ZERO_TRADES_PNL = []
NEGATIVE_PNL = [-3.0, -2.5, -1.8]

ZERO_TRADES_LIST = []

ONE_TRADE_DETAILED = [
    {"date": "2024-01-15", "symbol": "AAPL", "action": "BUY",  "price": 185.50, "shares": 10},
    {"date": "2024-02-20", "symbol": "AAPL", "action": "SELL", "price": 195.20, "shares": 10},
]

NEGATIVE_TRADE_DETAILED = [
    {"date": "2024-01-15", "symbol": "AAPL", "action": "BUY",  "price": 200.0, "shares": 10},
    {"date": "2024-02-20", "symbol": "AAPL", "action": "SELL", "price": 185.0, "shares": 10},
]

# statistical_tests — run_significance_tests

class TestRunSignificanceTestsEdgeCases:
    def test_zero_trades_returns_dict(self):
        result = run_significance_tests(ZERO_TRADES_PNL)
        assert isinstance(result, dict)

    def test_zero_trades_has_verdict(self):
        result = run_significance_tests(ZERO_TRADES_PNL)
        assert "verdict" in result

    def test_zero_trades_verdict_is_insufficient(self):
        result = run_significance_tests(ZERO_TRADES_PNL)
        assert result["verdict"] == "INSUFFICIENT_DATA"

    def test_one_trade_returns_dict(self):
        result = run_significance_tests(ONE_TRADE_PNL)
        assert isinstance(result, dict)

    def test_one_trade_has_verdict(self):
        result = run_significance_tests(ONE_TRADE_PNL)
        assert "verdict" in result

    def test_one_trade_verdict_is_insufficient(self):
        result = run_significance_tests(ONE_TRADE_PNL)
        assert result["verdict"] == "INSUFFICIENT_DATA"

    def test_negative_returns_returns_dict(self):
        result = run_significance_tests(NEGATIVE_PNL)
        assert isinstance(result, dict)

    def test_negative_returns_has_verdict(self):
        result = run_significance_tests(NEGATIVE_PNL)
        assert "verdict" in result

    def test_negative_returns_warns_about_negative_mean(self):
        result = run_significance_tests(NEGATIVE_PNL)
        assert any("negative" in w.lower() for w in result.get("warnings", []))


# overfitting_detector — detect_overfitting

class TestDetectOverfittingEdgeCases:
    def test_zero_trades_returns_dict(self):
        result = detect_overfitting(ZERO_TRADES_PNL)
        assert isinstance(result, dict)

    def test_zero_trades_has_score(self):
        result = detect_overfitting(ZERO_TRADES_PNL)
        assert "overfitting_score" in result

    def test_zero_trades_score_is_zero(self):
        result = detect_overfitting(ZERO_TRADES_PNL)
        assert result["overfitting_score"] == 0.0

    def test_one_trade_returns_dict(self):
        result = detect_overfitting(ONE_TRADE_PNL)
        assert isinstance(result, dict)

    def test_one_trade_has_score(self):
        result = detect_overfitting(ONE_TRADE_PNL)
        assert "overfitting_score" in result

    def test_one_trade_score_in_valid_range(self):
        result = detect_overfitting(ONE_TRADE_PNL)
        assert 0.0 <= result["overfitting_score"] <= 100.0

    def test_negative_returns_returns_dict(self):
        result = detect_overfitting(NEGATIVE_PNL)
        assert isinstance(result, dict)

    def test_negative_returns_has_score(self):
        result = detect_overfitting(NEGATIVE_PNL)
        assert "overfitting_score" in result

    def test_negative_returns_score_in_valid_range(self):
        result = detect_overfitting(NEGATIVE_PNL)
        assert 0.0 <= result["overfitting_score"] <= 100.0

    def test_negative_returns_has_risk_tier(self):
        result = detect_overfitting(NEGATIVE_PNL)
        assert "risk_tier" in result
        assert isinstance(result["risk_tier"], str)


# transaction_costs — calculate_real_costs

class TestCalculateRealCostsEdgeCases:
    def test_zero_trades_returns_dict(self):
        result = calculate_real_costs(ZERO_TRADES_LIST, account_size=10_000)
        assert isinstance(result, dict)

    def test_zero_trades_has_cost_summary(self):
        result = calculate_real_costs(ZERO_TRADES_LIST, account_size=10_000)
        assert "cost_summary" in result

    def test_zero_trades_total_costs_are_zero(self):
        result = calculate_real_costs(ZERO_TRADES_LIST, account_size=10_000)
        assert result["cost_summary"]["total_trading_costs_usd"] == 0.0

    def test_one_trade_returns_dict(self):
        result = calculate_real_costs(ONE_TRADE_DETAILED, account_size=10_000)
        assert isinstance(result, dict)

    def test_one_trade_has_adjusted_returns(self):
        result = calculate_real_costs(ONE_TRADE_DETAILED, account_size=10_000)
        assert "adjusted_returns" in result

    def test_one_trade_commissions_are_positive(self):
        result = calculate_real_costs(ONE_TRADE_DETAILED, account_size=10_000)
        assert result["commissions"]["total_commission_usd"] > 0

    def test_negative_returns_returns_dict(self):
        result = calculate_real_costs(NEGATIVE_TRADE_DETAILED, account_size=10_000)
        assert isinstance(result, dict)

    def test_negative_returns_has_adjusted_returns(self):
        result = calculate_real_costs(NEGATIVE_TRADE_DETAILED, account_size=10_000)
        assert "adjusted_returns" in result

    def test_negative_returns_gross_profit_is_negative(self):
        result = calculate_real_costs(NEGATIVE_TRADE_DETAILED, account_size=10_000)
        assert result["adjusted_returns"]["gross_profit_usd"] < 0
