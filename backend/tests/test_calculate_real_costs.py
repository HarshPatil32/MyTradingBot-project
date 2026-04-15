"""
Tests for calculate_real_costs() adjusted return math.
Covers multi-trade scenarios with mixed short/long term holds.
"""
import pytest
from transaction_costs import calculate_real_costs, CostConfig

ACCOUNT_SIZE = 10_000.0

# Deterministic dates:
#   BUY_DATE -> SHORT_SELL_DATE = 181 days  (< 365, short-term)
#   BUY_DATE -> LONG_SELL_DATE  = 425 days  (> 365, long-term)
BUY_DATE = "2024-01-01"
SHORT_SELL_DATE = "2024-06-30"  # (date(2024,6,30) - date(2024,1,1)).days == 181
LONG_SELL_DATE = "2025-03-01"   # (date(2025,3,1) - date(2024,1,1)).days == 425


def _no_costs():
    """Zero out all friction including taxes."""
    return CostConfig(
        commission_per_trade=0.0,
        slippage_pct=0.0,
        spread_pct=0.0,
        apply_taxes=False,
    )


def _no_trading_costs():
    """Zero trading friction but taxes still applied."""
    return CostConfig(
        commission_per_trade=0.0,
        slippage_pct=0.0,
        spread_pct=0.0,
        apply_taxes=True,
    )


# Three-trade fixture:
#   AAPL: BUY 10@100, SELL 10@130, 181 days  → profit +$300 (short-term)
#   MSFT: BUY  5@200, SELL  5@180, 181 days  → profit  -$100 (loss)
#   GOOG: BUY  8@150, SELL  8@200, 425 days  → profit +$400 (long-term)
#
# Trade legs + values: 1000+1300+1000+900+1200+1600 = 7000
# gross_profit = 300 - 100 + 400 = $600  →  gross_return = 6.0%
# short_gains=$300  short_tax=$111 (×0.37)
# long_gains=$400   long_tax=$80  (×0.20)
# total_tax=$191
# commissions = 6×$1 = $6
# slippage    = 7000×0.008 = $56
# spread      = 7000×0.002 = $14
# total_trading_costs=$76   total_all_costs=$267
MIXED_TRADES = [
    {"date": BUY_DATE,        "symbol": "AAPL", "action": "BUY",  "price": 100.0, "shares": 10},
    {"date": SHORT_SELL_DATE, "symbol": "AAPL", "action": "SELL", "price": 130.0, "shares": 10},
    {"date": BUY_DATE,        "symbol": "MSFT", "action": "BUY",  "price": 200.0, "shares": 5},
    {"date": SHORT_SELL_DATE, "symbol": "MSFT", "action": "SELL", "price": 180.0, "shares": 5},
    {"date": BUY_DATE,        "symbol": "GOOG", "action": "BUY",  "price": 150.0, "shares": 8},
    {"date": LONG_SELL_DATE,  "symbol": "GOOG", "action": "SELL", "price": 200.0, "shares": 8},
]


# ---------------------------------------------------------------------------
# Gross return
# ---------------------------------------------------------------------------

class TestGrossReturn:
    def test_gross_profit_sums_round_trip_profits(self):
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE, _no_costs())
        assert result["adjusted_returns"]["gross_profit_usd"] == pytest.approx(600.0)

    def test_gross_return_pct_is_profit_over_account_size(self):
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE, _no_costs())
        assert result["adjusted_returns"]["gross_return_pct"] == pytest.approx(6.0)


# Tax calculation for mixed holds

class TestTaxCalculation:
    def test_short_term_gains_taxed_at_37_pct(self):
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE, _no_trading_costs())
        taxes = result["taxes"]
        assert taxes["short_term_gains_usd"] == pytest.approx(300.0)
        assert taxes["short_term_tax_usd"] == pytest.approx(111.0)  # 300 * 0.37

    def test_long_term_gains_taxed_at_20_pct(self):
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE, _no_trading_costs())
        taxes = result["taxes"]
        assert taxes["long_term_gains_usd"] == pytest.approx(400.0)
        assert taxes["long_term_tax_usd"] == pytest.approx(80.0)  # 400 * 0.20

    def test_losses_are_tracked_but_do_not_offset_gains(self):
        # Conservative: losses are recorded but not netted against gains.
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE, _no_trading_costs())
        taxes = result["taxes"]
        assert taxes["total_losses_usd"] == pytest.approx(100.0)
        assert taxes["total_tax_usd"] == pytest.approx(191.0)  # still full 111+80

    def test_exactly_365_day_hold_is_short_term(self):
        # IRS rule: hold must be MORE than 12 months (> 365 days) for long-term.
        # 2023-01-01 to 2024-01-01 = 365 days exactly → should be short-term.
        trades = [
            {"date": "2023-01-01", "symbol": "AAPL", "action": "BUY",  "price": 100.0, "shares": 10},
            {"date": "2024-01-01", "symbol": "AAPL", "action": "SELL", "price": 120.0, "shares": 10},
        ]
        result = calculate_real_costs(trades, ACCOUNT_SIZE, _no_trading_costs())
        taxes = result["taxes"]
        assert taxes["short_term_tax_usd"] == pytest.approx(74.0)  # $200 * 0.37
        assert taxes["long_term_tax_usd"] == pytest.approx(0.0)

    def test_366_day_hold_is_long_term(self):
        # 2024-01-01 to 2025-01-02 = 367 days (2024 is a leap year) → long-term.
        trades = [
            {"date": "2024-01-01", "symbol": "AAPL", "action": "BUY",  "price": 100.0, "shares": 10},
            {"date": "2025-01-02", "symbol": "AAPL", "action": "SELL", "price": 120.0, "shares": 10},
        ]
        result = calculate_real_costs(trades, ACCOUNT_SIZE, _no_trading_costs())
        taxes = result["taxes"]
        assert taxes["long_term_tax_usd"] == pytest.approx(40.0)  # $200 * 0.20
        assert taxes["short_term_tax_usd"] == pytest.approx(0.0)


# Adjusted return math (internal consistency)

class TestAdjustedReturnMath:
    def test_after_costs_profit_equals_gross_minus_trading_costs(self):
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE)
        adj = result["adjusted_returns"]
        cs = result["cost_summary"]
        assert adj["after_costs_profit_usd"] == pytest.approx(
            adj["gross_profit_usd"] - cs["total_trading_costs_usd"], rel=1e-5
        )

    def test_after_costs_and_tax_profit_equals_gross_minus_all_costs(self):
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE)
        adj = result["adjusted_returns"]
        cs = result["cost_summary"]
        assert adj["after_costs_and_tax_profit_usd"] == pytest.approx(
            adj["gross_profit_usd"] - cs["total_all_costs_usd"], rel=1e-5
        )

    def test_after_costs_pct_consistent_with_usd(self):
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE)
        adj = result["adjusted_returns"]
        expected_pct = adj["after_costs_profit_usd"] / ACCOUNT_SIZE * 100
        assert adj["after_costs_pct"] == pytest.approx(expected_pct, rel=1e-5)

    def test_after_costs_and_tax_pct_consistent_with_usd(self):
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE)
        adj = result["adjusted_returns"]
        expected_pct = adj["after_costs_and_tax_profit_usd"] / ACCOUNT_SIZE * 100
        assert adj["after_costs_and_tax_pct"] == pytest.approx(expected_pct, rel=1e-5)

    def test_zero_costs_adjusted_return_equals_gross(self):
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE, _no_costs())
        adj = result["adjusted_returns"]
        assert adj["after_costs_pct"] == pytest.approx(adj["gross_return_pct"])
        assert adj["after_costs_and_tax_pct"] == pytest.approx(adj["gross_return_pct"])

    def test_costs_always_reduce_return(self):
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE)
        adj = result["adjusted_returns"]
        assert adj["after_costs_pct"] < adj["gross_return_pct"]
        assert adj["after_costs_and_tax_pct"] < adj["after_costs_pct"]

    def test_exact_after_tax_return_no_trading_friction(self):
        # gross=$600 (6.0%), tax=$191 → after_tax = $409 = 4.09%
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE, _no_trading_costs())
        adj = result["adjusted_returns"]
        assert adj["gross_return_pct"] == pytest.approx(6.0)
        assert adj["after_costs_and_tax_profit_usd"] == pytest.approx(409.0)
        assert adj["after_costs_and_tax_pct"] == pytest.approx(4.09, rel=1e-3)

    def test_exact_after_all_costs_return_default_config(self):
        # trading_costs=$76 (0.76%), tax=$191 → total=$267 (2.67%)
        # after_costs_pct=5.24%, after_costs_and_tax_pct=3.33%
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE)
        adj = result["adjusted_returns"]
        cs = result["cost_summary"]
        assert cs["total_trading_costs_usd"] == pytest.approx(76.0, rel=1e-3)
        assert cs["total_all_costs_usd"] == pytest.approx(267.0, rel=1e-3)
        assert adj["after_costs_pct"] == pytest.approx(5.24, rel=1e-3)
        assert adj["after_costs_and_tax_pct"] == pytest.approx(3.33, rel=1e-3)


# Cost summary integrity

class TestCostSummaryIntegrity:
    def test_total_all_costs_equals_trading_costs_plus_tax(self):
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE)
        cs = result["cost_summary"]
        assert cs["total_all_costs_usd"] == pytest.approx(
            cs["total_trading_costs_usd"] + cs["total_tax_usd"], rel=1e-5
        )

    def test_breakdown_pcts_sum_to_total_all_costs_pct(self):
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE)
        cs = result["cost_summary"]
        b = cs["breakdown_pct"]
        total = b["commissions"] + b["slippage"] + b["bid_ask_spread"] + b["taxes"]
        assert cs["total_all_costs_pct"] == pytest.approx(total, rel=1e-3)

    def test_trading_costs_pct_equals_usd_over_account_size(self):
        result = calculate_real_costs(MIXED_TRADES, ACCOUNT_SIZE)
        cs = result["cost_summary"]
        assert cs["total_trading_costs_pct"] == pytest.approx(
            cs["total_trading_costs_usd"] / ACCOUNT_SIZE * 100, rel=1e-5
        )
