"""Tests for parse_detailed() in csv_analyzer."""
import pytest

from csv_analyzer import parse_detailed, FREE_TIER_TRADE_LIMIT


VALID_CSV = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,185.50,10\n2024-02-20,AAPL,SELL,195.20,10\n"


class TestParseDetailedHappyPath:
    def test_returns_list(self):
        result = parse_detailed(VALID_CSV)
        assert isinstance(result, list)

    def test_correct_row_count(self):
        result = parse_detailed(VALID_CSV)
        assert len(result) == 2

    def test_date_preserved_as_string(self):
        result = parse_detailed(VALID_CSV)
        assert result[0]["date"] == "2024-01-15"

    def test_symbol_uppercased(self):
        result = parse_detailed(VALID_CSV)
        assert result[0]["symbol"] == "AAPL"

    def test_action_value(self):
        result = parse_detailed(VALID_CSV)
        assert result[0]["action"] == "BUY"
        assert result[1]["action"] == "SELL"

    def test_price_is_float(self):
        result = parse_detailed(VALID_CSV)
        assert isinstance(result[0]["price"], float)
        assert result[0]["price"] == 185.50

    def test_shares_is_float(self):
        result = parse_detailed(VALID_CSV)
        assert isinstance(result[0]["shares"], float)
        assert result[0]["shares"] == 10.0

    def test_header_only_returns_empty_list(self):
        result = parse_detailed("date,symbol,action,price,shares\n")
        assert result == []

    def test_fractional_shares_accepted(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,TSLA,BUY,250.00,0.5\n"
        result = parse_detailed(csv_data)
        assert result[0]["shares"] == 0.5


class TestParseDetailedColumnHandling:
    def test_mixed_case_headers(self):
        csv_data = "Date,Symbol,Action,Price,Shares\n2024-01-15,AAPL,BUY,185.50,10\n"
        result = parse_detailed(csv_data)
        assert len(result) == 1

    def test_padded_headers(self):
        csv_data = " date , symbol , action , price , shares \n2024-01-15,AAPL,BUY,185.50,10\n"
        result = parse_detailed(csv_data)
        assert len(result) == 1

    def test_extra_columns_ignored(self):
        csv_data = "date,symbol,action,price,shares,notes,broker\n2024-01-15,AAPL,BUY,185.50,10,entry,TD\n"
        result = parse_detailed(csv_data)
        assert len(result) == 1
        assert "notes" not in result[0]

    def test_missing_column_raises(self):
        csv_data = "date,symbol,action,price\n2024-01-15,AAPL,BUY,185.50\n"
        with pytest.raises(ValueError, match="missing required columns"):
            parse_detailed(csv_data)

    def test_empty_csv_raises(self):
        with pytest.raises(ValueError):
            parse_detailed("")


class TestParseDetailedDateValidation:
    def test_slash_format_raises(self):
        csv_data = "date,symbol,action,price,shares\n01/15/2024,AAPL,BUY,185.50,10\n"
        with pytest.raises(ValueError, match="Row 2: invalid date"):
            parse_detailed(csv_data)

    def test_missing_leading_zero_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-1-5,AAPL,BUY,185.50,10\n"
        with pytest.raises(ValueError, match="Row 2: invalid date"):
            parse_detailed(csv_data)

    def test_error_message_includes_bad_value(self):
        bad_date = "15-01-2024"
        csv_data = f"date,symbol,action,price,shares\n{bad_date},AAPL,BUY,185.50,10\n"
        with pytest.raises(ValueError, match=bad_date):
            parse_detailed(csv_data)


class TestParseDetailedActionValidation:
    def test_lowercase_buy_normalized(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,buy,185.50,10\n"
        result = parse_detailed(csv_data)
        assert result[0]["action"] == "BUY"

    def test_mixed_case_sell_normalized(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,Sell,185.50,10\n"
        result = parse_detailed(csv_data)
        assert result[0]["action"] == "SELL"

    def test_invalid_action_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,HOLD,185.50,10\n"
        with pytest.raises(ValueError, match="Row 2: action 'HOLD' is not BUY or SELL"):
            parse_detailed(csv_data)

    def test_blank_action_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,,185.50,10\n"
        with pytest.raises(ValueError, match="Row 2: action is blank"):
            parse_detailed(csv_data)


class TestParseDetailedPriceValidation:
    def test_zero_price_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,0,10\n"
        with pytest.raises(ValueError, match="price must be positive"):
            parse_detailed(csv_data)

    def test_negative_price_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,-5.00,10\n"
        with pytest.raises(ValueError, match="price must be positive"):
            parse_detailed(csv_data)

    def test_non_numeric_price_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,N/A,10\n"
        with pytest.raises(ValueError, match="Row 2: price 'N/A' is not a number"):
            parse_detailed(csv_data)

    def test_inf_price_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,inf,10\n"
        with pytest.raises(ValueError, match="price must be positive"):
            parse_detailed(csv_data)

    def test_nan_price_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,nan,10\n"
        with pytest.raises(ValueError, match="price must be positive"):
            parse_detailed(csv_data)


class TestParseDetailedSharesValidation:
    def test_zero_shares_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,185.50,0\n"
        with pytest.raises(ValueError, match="shares must be positive"):
            parse_detailed(csv_data)

    def test_negative_shares_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,185.50,-1\n"
        with pytest.raises(ValueError, match="shares must be positive"):
            parse_detailed(csv_data)

    def test_non_numeric_shares_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,185.50,ten\n"
        with pytest.raises(ValueError, match="Row 2: shares 'ten' is not a number"):
            parse_detailed(csv_data)

    def test_inf_shares_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,185.50,inf\n"
        with pytest.raises(ValueError, match="shares must be positive"):
            parse_detailed(csv_data)

    def test_nan_shares_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,185.50,nan\n"
        with pytest.raises(ValueError, match="shares must be positive"):
            parse_detailed(csv_data)


class TestParseDetailedSymbolValidation:
    def test_blank_symbol_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,,BUY,185.50,10\n"
        with pytest.raises(ValueError, match="Row 2: symbol is blank"):
            parse_detailed(csv_data)

    def test_lowercase_symbol_uppercased(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,aapl,BUY,185.50,10\n"
        result = parse_detailed(csv_data)
        assert result[0]["symbol"] == "AAPL"

    def test_symbol_with_dot_accepted(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,BRK.B,BUY,200.00,5\n"
        result = parse_detailed(csv_data)
        assert result[0]["symbol"] == "BRK.B"

    def test_symbol_with_hyphen_accepted(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,BRK-B,BUY,200.00,5\n"
        result = parse_detailed(csv_data)
        assert result[0]["symbol"] == "BRK-B"

    def test_symbol_with_special_chars_raises(self):
        bad_symbols = [
            "AAPL!",   # special char
            "123",     # digits only
            "AAPL.",   # trailing dot
            "AA PL",   # space
            "A" * 21,  # too long
        ]
        for bad in bad_symbols:
            csv_data = f"date,symbol,action,price,shares\n2024-01-15,{bad},BUY,185.50,10\n"
            with pytest.raises(ValueError, match="invalid characters"):
                parse_detailed(csv_data)
        # Empty string triggers 'symbol is blank'
        csv_data = "date,symbol,action,price,shares\n2024-01-15,,BUY,185.50,10\n"
        with pytest.raises(ValueError, match="symbol is blank"):
            parse_detailed(csv_data)


class TestParseDetailedBlankRows:
    def test_blank_row_in_middle_skipped(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,185.50,10\n,,,,\n2024-02-20,AAPL,SELL,195.20,10\n"
        result = parse_detailed(csv_data)
        assert len(result) == 2


class TestParseDetailedFreeTierLimit:
    def test_over_limit_raises(self):
        header = "date,symbol,action,price,shares\n"
        rows = "".join(
            f"2024-01-{(i % 28) + 1:02d},AAPL,BUY,100.00,1\n"
            for i in range(FREE_TIER_TRADE_LIMIT + 1)
        )
        with pytest.raises(ValueError, match=f"exceeds the free tier limit of {FREE_TIER_TRADE_LIMIT}"):
            parse_detailed(header + rows)

    def test_exactly_at_limit_passes(self):
        header = "date,symbol,action,price,shares\n"
        rows = "".join(
            f"2024-01-{(i % 28) + 1:02d},AAPL,BUY,100.00,1\n"
            for i in range(FREE_TIER_TRADE_LIMIT)
        )
        result = parse_detailed(header + rows)
        assert len(result) == FREE_TIER_TRADE_LIMIT

    def test_blank_rows_after_limit_not_counted(self):
        # 100 valid trades followed by blank rows must not raise
        header = "date,symbol,action,price,shares\n"
        rows = "".join(
            f"2024-01-{(i % 28) + 1:02d},AAPL,BUY,100.00,1\n"
            for i in range(FREE_TIER_TRADE_LIMIT)
        )
        trailing_blanks = ",,,,\n,,,,\n"
        result = parse_detailed(header + rows + trailing_blanks)
        assert len(result) == FREE_TIER_TRADE_LIMIT


class TestParseDetailedWhitespaceCells:
    def test_whitespace_padded_data_cells_parsed(self):
        csv_data = "date,symbol,action,price,shares\n  2024-01-15  ,  AAPL  ,  BUY  ,  185.50  ,  10  \n"
        result = parse_detailed(csv_data)
        assert len(result) == 1
        assert result[0]["date"] == "2024-01-15"
        assert result[0]["symbol"] == "AAPL"
        assert result[0]["action"] == "BUY"
        assert result[0]["price"] == 185.50
        assert result[0]["shares"] == 10.0


class TestParseDetailedRaggedRows:
    def test_short_row_raises_value_error(self):
        # DictReader fills missing trailing cells with None; must raise a clear ValueError
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL\n"
        with pytest.raises(ValueError) as excinfo:
            parse_detailed(csv_data)
        assert "Row 2" in str(excinfo.value)

    def test_short_row_missing_only_last_field_raises(self):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,185.50\n"
        with pytest.raises(ValueError) as excinfo:
            parse_detailed(csv_data)
        assert "Row 2" in str(excinfo.value)
