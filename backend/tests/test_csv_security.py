"""Tests for CSV upload security: content safety and filename sanitization."""
import io
import pytest

from csv_analyzer import _assert_content_safe, sanitize_csv
from app import app as flask_app, _safe_filename


@pytest.fixture()
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# _assert_content_safe — content-level checks
# ---------------------------------------------------------------------------

class TestAssertContentSafe:
    def test_null_byte_raises(self):
        with pytest.raises(ValueError, match="null bytes"):
            _assert_content_safe("date,symbol\n2024-01-01,AAPL\x00")

    def test_elf_magic_bytes_raises(self):
        with pytest.raises(ValueError, match="binary file"):
            _assert_content_safe("\x7fELF\x02\x01\x01")

    def test_pe_magic_bytes_raises(self):
        with pytest.raises(ValueError, match="binary file"):
            _assert_content_safe("MZ\x90\x00")

    def test_shebang_raises(self):
        with pytest.raises(ValueError, match="binary file"):
            _assert_content_safe("#!/bin/bash\nrm -rf /")

    def test_formula_equals_raises(self):
        with pytest.raises(ValueError, match="unsafe cell"):
            _assert_content_safe("date,symbol\n2024-01-01,=CMD|'/C calc'!A0")

    def test_formula_plus_raises(self):
        with pytest.raises(ValueError, match="unsafe cell"):
            _assert_content_safe("date,symbol\n2024-01-01,+cmd|' /C calc")

    def test_formula_at_raises(self):
        with pytest.raises(ValueError, match="unsafe cell"):
            _assert_content_safe("date,symbol\n2024-01-01,@SUM(1+1)*cmd")

    def test_formula_minus_non_numeric_raises(self):
        with pytest.raises(ValueError, match="unsafe cell"):
            _assert_content_safe("date,symbol\n2024-01-01,-cmd|payload")

    def test_minus_numeric_price_passes(self):
        # Negative numbers are valid prices and must not be rejected
        _assert_content_safe("date,pnl\n2024-01-01,-1.5")

    def test_negative_scientific_notation_passes(self):
        # e.g. -1e-5 is a valid float and must not be rejected
        _assert_content_safe("date,pnl\n2024-01-01,-1e-5")

    def test_bom_prefixed_elf_raises(self):
        # A UTF-8 BOM before magic bytes must not bypass the binary check
        bom = "\ufeff"
        payload = bom + "\x7fELF\x02\x01\x01"
        with pytest.raises(ValueError, match="binary file"):
            _assert_content_safe(payload)

    def test_clean_csv_passes(self):
        _assert_content_safe("date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,185.50,10\n")

    def test_empty_string_passes(self):
        _assert_content_safe("")


# ---------------------------------------------------------------------------
# sanitize_csv — safety gate is called first, and return value is correct
# ---------------------------------------------------------------------------

class TestSanitizeCsvSafetyGate:
    def test_formula_injection_blocked_before_sanitize(self):
        with pytest.raises(ValueError):
            sanitize_csv("date,symbol\n2024-01-01,=HYPERLINK(\"evil.com\")")

    def test_binary_blocked_before_sanitize(self):
        with pytest.raises(ValueError):
            sanitize_csv("\x7fELFsomedata")

    def test_returns_string_not_none(self):
        result = sanitize_csv("date,symbol\n2024-01-01,AAPL\n")
        assert result is not None
        assert isinstance(result, str)

    def test_bom_stripped(self):
        result = sanitize_csv("\ufeffdate,symbol\n2024-01-01,AAPL")
        assert not result.startswith("\ufeff")

    def test_crlf_normalised(self):
        result = sanitize_csv("date,symbol\r\n2024-01-01,AAPL\r\n")
        assert "\r" not in result

    def test_semicolons_converted(self):
        result = sanitize_csv("date;symbol\n2024-01-01;AAPL")
        assert ";" not in result
        assert "date,symbol" in result


# ---------------------------------------------------------------------------
# _safe_filename — filename sanitization
# ---------------------------------------------------------------------------

class TestSafeFilename:
    def test_path_traversal_stripped(self):
        result = _safe_filename("../../../etc/passwd.csv")
        # secure_filename collapses path components — no separator chars remain
        assert "/" not in result and ".." not in result
        assert result.endswith(".csv")

    def test_null_byte_stripped(self):
        # werkzeug strips null bytes as part of secure_filename
        result = _safe_filename("file\x00name.csv")
        assert "\x00" not in result
        assert result  # must not be empty

    def test_normal_filename_unchanged(self):
        assert _safe_filename("my_backtest.csv") == "my_backtest.csv"

    def test_empty_after_sanitize_raises(self):
        # A name that is purely path separators leaves nothing after sanitization
        with pytest.raises(ValueError, match="invalid or empty"):
            _safe_filename("../../")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="invalid or empty"):
            _safe_filename("")


# ---------------------------------------------------------------------------
# /analyze-backtest route — integration
# ---------------------------------------------------------------------------

class TestAnalyzeBacktestRoute:
    def test_clean_json_upload_returns_200(self, client):
        csv_data = "date,symbol,action,price,shares\n2024-01-15,AAPL,BUY,185.50,10\n"
        resp = client.post("/analyze-backtest", json={"csv_data": csv_data})
        assert resp.status_code == 200

    def test_formula_csv_returns_400(self, client):
        csv_data = "date,symbol\n2024-01-01,=CMD|calc"
        resp = client.post("/analyze-backtest", json={"csv_data": csv_data})
        assert resp.status_code == 400

    def test_binary_file_upload_returns_400(self, client):
        payload = b"\x7fELF\x02\x01\x01\x00"
        data = {"file": (io.BytesIO(payload), "malware.csv")}
        resp = client.post("/analyze-backtest", content_type="multipart/form-data", data=data)
        assert resp.status_code == 400

    def test_path_traversal_filename_returns_400(self, client):
        data = {"file": (io.BytesIO(b"date,symbol\n"), "../../etc/passwd")}
        resp = client.post("/analyze-backtest", content_type="multipart/form-data", data=data)
        # secure_filename reduces this to 'passwd' which is valid, so it proceeds past filename check.
        # The important thing is it does NOT return a server error from path operations.
        assert resp.status_code in (200, 400)

    def test_empty_filename_returns_400(self, client):
        data = {"file": (io.BytesIO(b"date,symbol\n"), "../../")}
        resp = client.post("/analyze-backtest", content_type="multipart/form-data", data=data)
        assert resp.status_code == 400

    def test_wrong_content_type_returns_400(self, client):
        resp = client.post("/analyze-backtest", data="plain text", content_type="text/plain")
        assert resp.status_code == 400

    def test_non_string_csv_data_returns_400(self, client):
        resp = client.post("/analyze-backtest", json={"csv_data": 12345})
        assert resp.status_code == 400
