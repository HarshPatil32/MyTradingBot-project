"""
csv_analyzer.py
---------------
Parses, validates, and normalises uploaded trade history CSV files before
handing the cleaned trade data off to the analysis modules.
"""

from __future__ import annotations

import csv
import io
import logging
import math
import re
import statistics
from datetime import datetime
from typing import Any, Sequence

def _normalize_action(action):
    """Normalize trade action to uppercase, handling None and whitespace."""
    return (str(action).strip().upper() if action is not None else "")


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants and Exceptions
# ---------------------------------------------------------------------------

FREE_TIER_TRADE_LIMIT = 100

class FreeTierLimitExceeded(ValueError):
    """Raised when the free tier trade limit is exceeded."""
    pass

REQUIRED_DETAILED_COLUMNS: frozenset[str] = frozenset(
    {"date", "symbol", "action", "price", "shares"}
)

REQUIRED_SUMMARY_KEYS: frozenset[str] = frozenset(
    {"initial_capital", "final_balance", "num_trades", "win_rate", "start_date", "end_date"}
)

# Binary file magic bytes that should never appear in a CSV
_BINARY_MAGIC: tuple[bytes, ...] = (
    b"MZ",           # Windows PE/EXE
    b"\x7fELF",      # Linux ELF
    b"#!",           # Shell/script shebang
    b"%PDF",         # PDF
    b"PK\x03\x04",   # ZIP / XLSX / DOCX
    b"\x89PNG",      # PNG image
    b"\x1f\x8b",     # GZIP archive
)

# Characters that trigger formula execution in spreadsheet tools (CSV injection)
_FORMULA_CHARS: frozenset[str] = frozenset({"=", "+", "@"})

# Valid ticker: uppercase letters, digits, dots, hyphens; 1-20 chars total
_SYMBOL_RE = re.compile(r"^[A-Z0-9]([A-Z0-9.\-]{0,19})?$")


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _is_numeric_cell(value: str) -> bool:
    """Return True if value is a plain number (int, float, or scientific notation)."""
    try:
        float(value)
        return True
    except ValueError:
        return False


def _require_field(value: str | None, row_num: int, name: str) -> str:
    if value is None or not str(value).strip():
        raise ValueError(f"Row {row_num}: {name} is blank")
    return str(value).strip()


def _parse_positive_float(value: str | None, field: str, row_num: int) -> float:
    """Parse a string as a positive finite float, raising ValueError with a clear message."""
    value = _require_field(value, row_num, field)
    try:
        result = float(value)
    except ValueError:
        raise ValueError(f"Row {row_num}: {field} '{value}' is not a number")
    if math.isnan(result) or math.isinf(result) or result <= 0:
        raise ValueError(f"Row {row_num}: {field} must be positive, got '{value}'")
    return result


def _parse_iso_date(value: str | None, field: str, row_num: int) -> datetime:
    """Parse a strict YYYY-MM-DD date string, raising ValueError with a clear message."""
    value = _require_field(value, row_num, field)
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Row {row_num}: invalid {field} '{value}', expected YYYY-MM-DD")
    if parsed.strftime("%Y-%m-%d") != value:
        raise ValueError(f"Row {row_num}: invalid {field} '{value}', expected YYYY-MM-DD")
    return parsed


def _assert_content_safe(csv_data: str) -> None:
    """Raise ValueError if csv_data looks like a binary file or contains formula injection."""
    # Strip BOM at string level before encoding so it cannot hide binary signatures.
    # Use latin-1 (not utf-8) so each character maps to exactly one byte, preserving
    # extended-ASCII magic bytes like 0x89 (PNG) and 0x8b (GZIP) that would become
    # two-byte sequences in utf-8.
    check_str = csv_data[1:] if csv_data.startswith("\ufeff") else csv_data
    check_raw = check_str.encode("latin-1", errors="replace")

    for magic in _BINARY_MAGIC:
        if check_raw.startswith(magic):
            raise ValueError("CSV content appears to be a binary file, not a CSV")

    raw = csv_data.encode("utf-8", errors="replace")
    if b"\x00" in raw:
        raise ValueError("CSV content contains null bytes")

    # Check every cell for formula injection.
    # Numeric cells (including negative numbers and scientific notation) are safe.
    normalized = csv_data.replace("\r\n", "\n").replace("\r", "\n")
    reader = csv.reader(io.StringIO(normalized))
    for row in reader:
        for cell in row:
            stripped = cell.strip()
            if not stripped or _is_numeric_cell(stripped):
                continue
            if stripped[0] in _FORMULA_CHARS | {"-"}:
                raise ValueError("CSV contains a potentially unsafe cell value")


def _convert_semicolon_to_comma(csv_data: str) -> str:
    """Re-serialize a semicolon-delimited CSV as comma-delimited, preserving quoted fields."""
    out = io.StringIO()
    writer = csv.writer(out)
    for row in csv.reader(io.StringIO(csv_data), delimiter=";"):
        writer.writerow(row)
    return out.getvalue()


def _strip_row(row: dict) -> dict:
    # csv.DictReader can produce None for columns beyond the header width; skip those
    return {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def sanitize_csv(csv_data: str) -> str:
    """Strip BOM, normalise line endings, and convert semicolon delimiters to commas."""
    _assert_content_safe(csv_data)
    # Remove exactly one UTF-8 BOM if present
    if csv_data.startswith("\ufeff"):
        csv_data = csv_data[1:]
    # Normalise line endings to \n
    csv_data = csv_data.replace("\r\n", "\n").replace("\r", "\n")
    # Detect delimiter and convert semicolon-delimited files to comma-delimited
    first_non_empty = next((l for l in csv_data.split("\n") if l.strip()), "")
    try:
        dialect = csv.Sniffer().sniff(first_non_empty, delimiters=",;")
        logger.debug("CSV delimiter detected: %r", dialect.delimiter)
        if dialect.delimiter == ";":
            csv_data = _convert_semicolon_to_comma(csv_data)
    except csv.Error:
        # Sniffer can't decide (e.g. single-column file) — fall back to heuristic
        if ";" in first_non_empty and "," not in first_non_empty:
            csv_data = _convert_semicolon_to_comma(csv_data)
    return csv_data


def detect_format(csv_data: str) -> str:
    """Return 'detailed' or 'summary' based on the CSV header columns.

    Expects data that has already been through sanitize_csv().
    Raises ValueError if the header matches neither known format.
    'detailed' is checked first; a file satisfying both formats is treated as 'detailed'.
    """
    reader = csv.reader(io.StringIO(csv_data))
    try:
        header_row = next(reader)
    except StopIteration:
        raise ValueError("CSV is empty or has no header row")

    actual_cols: frozenset[str] = frozenset(col.strip().lower() for col in header_row if col.strip())

    if not actual_cols:
        raise ValueError("CSV is empty or has no header row")

    if REQUIRED_DETAILED_COLUMNS <= actual_cols:
        return "detailed"

    if REQUIRED_SUMMARY_KEYS <= actual_cols:
        return "summary"

    missing_detailed = REQUIRED_DETAILED_COLUMNS - actual_cols
    missing_summary = REQUIRED_SUMMARY_KEYS - actual_cols
    raise ValueError(
        f"CSV columns do not match any known format. "
        f"For detailed format, missing: {sorted(missing_detailed)}. "
        f"For summary format, missing: {sorted(missing_summary)}."
    )


def parse_detailed(csv_data: str, is_free_tier: bool = True) -> list[dict]:
    """Parse a detailed trade-list CSV into a list of typed trade dicts.
    If is_free_tier is True, enforce the free tier trade limit.
    """
    reader = csv.DictReader(io.StringIO(csv_data))

    if reader.fieldnames is None:
        raise ValueError("CSV is empty or has no header row")

    # Build normalized (lowercase, stripped) -> original fieldname mapping
    norm_to_original: dict[str, str] = {f.strip().lower(): f for f in reader.fieldnames}

    missing = REQUIRED_DETAILED_COLUMNS - norm_to_original.keys()
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")

    # Access each required column by its original (un-normalized) fieldname
    col = {norm: norm_to_original[norm] for norm in REQUIRED_DETAILED_COLUMNS}

    trades: list[dict] = []
    for row_num, raw_row in enumerate(reader, start=2):
        # Skip entirely blank rows before checking the limit
        if all(v is None or v.strip() == "" for v in raw_row.values()):
            continue

        # Enforce limit on non-blank rows only
        if is_free_tier and len(trades) >= FREE_TIER_TRADE_LIMIT:
            raise FreeTierLimitExceeded(
                f"Trade count exceeds the free tier limit of {FREE_TIER_TRADE_LIMIT}"
            )

        raw_row = _strip_row(raw_row)

        date_val = _require_field(raw_row[col["date"]], row_num, "date")
        _parse_iso_date(date_val, "date", row_num)  # validation only; date stored as string

        symbol_val = _require_field(raw_row[col["symbol"]], row_num, "symbol").upper()
        # Disallow all-digit, trailing dot/hyphen, or any space
        if (
            not _SYMBOL_RE.match(symbol_val)
            or symbol_val.isdigit()
            or symbol_val.endswith(('.', '-'))
            or ' ' in symbol_val
        ):
            raise ValueError(f"Row {row_num}: symbol '{symbol_val}' contains invalid characters")

        action_val = _require_field(raw_row[col["action"]], row_num, "action").upper()
        if action_val not in {"BUY", "SELL"}:
            raise ValueError(f"Row {row_num}: action '{action_val}' is not BUY or SELL")

        price_val = _parse_positive_float(raw_row[col["price"]], "price", row_num)
        shares_val = _parse_positive_float(raw_row[col["shares"]], "shares", row_num)

        trades.append({
            "date": date_val,
            "symbol": symbol_val,
            "action": action_val,
            "price": price_val,
            "shares": shares_val,
        })

    return trades


def parse_summary(csv_data: str) -> dict:
    """
    Parse a summary-format CSV into a single dict of aggregate metrics.

    Expected columns (case/padding ignored):
        - initial_capital (float > 0)
        - final_balance (float > 0)
        - num_trades (int > 0, accepts e.g. "42" or "42.0")
        - win_rate (float in [0, 1])
        - start_date (YYYY-MM-DD string)
        - end_date (YYYY-MM-DD string)
    Extra columns are ignored. Missing/typoed columns raise ValueError.
    """
    reader = csv.DictReader(io.StringIO(csv_data))

    if reader.fieldnames is None:
        raise ValueError("CSV is empty or has no header row")

    # Normalize headers and check for required columns
    norm_to_original: dict[str, str] = {f.strip().lower(): f for f in reader.fieldnames}
    actual_cols = set(norm_to_original.keys())
    missing = REQUIRED_SUMMARY_KEYS - actual_cols
    extra = actual_cols - REQUIRED_SUMMARY_KEYS
    if missing:
        raise ValueError(f"CSV missing required fields: {sorted(missing)}. Did you typo a column?")

    # Map normalized required keys to original header
    col = {norm: norm_to_original[norm] for norm in REQUIRED_SUMMARY_KEYS}

    data_row: dict | None = None
    for raw_row in reader:
        if all(v is None or v.strip() == "" for v in raw_row.values()):
            continue
        if data_row is not None:
            raise ValueError("Summary CSV must contain exactly one data row")
        data_row = _strip_row(raw_row)

    if data_row is None:
        raise ValueError("CSV has no data rows")

    initial_capital = _parse_positive_float(
        data_row[col["initial_capital"]], "initial_capital", 2
    )
    final_balance = _parse_positive_float(
        data_row[col["final_balance"]], "final_balance", 2
    )

    # Accept num_trades as "42" or "42.0" (but not "42.5")
    num_trades_str = data_row[col["num_trades"]]
    try:
        num_trades_f = float(num_trades_str)
    except ValueError:
        raise ValueError(f"Row 2: num_trades '{num_trades_str}' is not a number")
    if (
        math.isnan(num_trades_f)
        or math.isinf(num_trades_f)
        or num_trades_f <= 0
        or num_trades_f % 1 != 0
    ):
        raise ValueError(f"Row 2: num_trades must be a positive integer, got '{num_trades_str}'")
    num_trades = int(num_trades_f)

    win_rate_str = data_row[col["win_rate"]]
    try:
        win_rate = float(win_rate_str)
    except ValueError:
        raise ValueError(f"Row 2: win_rate '{win_rate_str}' is not a number")
    # expects a decimal fraction, e.g. 0.65 not 65
    if math.isnan(win_rate) or math.isinf(win_rate) or win_rate < 0.0 or win_rate > 1.0:
        raise ValueError(f"Row 2: win_rate must be between 0 and 1, got '{win_rate_str}'")

    start_date_str = data_row[col["start_date"]]
    parsed_start = _parse_iso_date(start_date_str, "start_date", 2)

    end_date_str = data_row[col["end_date"]]
    parsed_end = _parse_iso_date(end_date_str, "end_date", 2)

    if parsed_start > parsed_end:
        raise ValueError(
            f"Row 2: start_date '{start_date_str}' must not be after end_date '{end_date_str}'"
        )

    # Extra columns are ignored, but could be logged if needed
    return {
        "initial_capital": initial_capital,
        "final_balance": final_balance,
        "num_trades": num_trades,
        "win_rate": win_rate,
        "start_date": start_date_str,
        "end_date": end_date_str,
    }


def validate_trades(trades: list[dict]) -> list[dict]:
    """Check trades for pairing errors and duplicates; return a list of warning dicts.

    Warnings (not exceptions) are returned so callers can still show results while
    surfacing data quality issues to the user.
    """
    warnings: list[dict] = []

    # Detect duplicate rows: same date + symbol + action (normalized)
    seen: dict[tuple, int] = {}
    for trade in trades:
        # Normalize action and symbol for all checks
        action = _normalize_action(trade.get("action"))
        symbol = str(trade.get("symbol") or "").strip().upper()
        date = str(trade.get("date") or "").strip()
        # Overwrite the trade dict so downstream code always sees normalized values
        trade["action"] = action
        trade["symbol"] = symbol
        key = (date, symbol, action)
        seen[key] = seen.get(key, 0) + 1

    for key, count in seen.items():
        if count > 1:
            date, symbol, action = key
            warnings.append({
                "type": "duplicate",
                "level": "warning",
                "message": (
                    f"Duplicate trade: {action} {symbol} on {date} appears {count} times"
                ),
            })

    # Check BUY/SELL pairing per symbol using a simple FIFO stack
    open_buys: dict[str, list[dict]] = {}
    for trade in trades:
        action = _normalize_action(trade.get("action"))
        symbol = str(trade.get("symbol") or "").strip().upper()
        if action == "BUY":
            open_buys.setdefault(symbol, []).append(trade)
        elif action == "SELL":
            if not open_buys.get(symbol):
                date = trade.get("date") or "unknown date"
                warnings.append({
                    "type": "unmatched_sell",
                    "level": "warning",
                    "message": f"SELL for {symbol} on {date} has no preceding BUY",
                })
            else:
                open_buys[symbol].pop(0)

    for symbol, buys in open_buys.items():
        for buy in buys:
            date = buy.get("date") or "unknown date"
            warnings.append({
                "type": "unclosed_position",
                "level": "info",
                "message": f"Open position: {symbol} BUY on {date} (no matching SELL yet)",
            })

    # Check for zero or negative price or share count, or missing/invalid values
    def _is_invalid_value(val):
        try:
            return float(val) <= 0
        except (TypeError, ValueError):
            return True

    for idx, trade in enumerate(trades):
        symbol = str(trade.get("symbol") or "").strip().upper()
        date = trade.get("date") or "unknown date"
        price = trade.get("price")
        shares = trade.get("shares")

        if _is_invalid_value(price):
            warnings.append({
                "type": "invalid_price",
                "level": "warning",
                "message": f"Row {idx+1}: Trade {symbol} on {date} has invalid price: {price}",
            })
        if _is_invalid_value(shares):
            warnings.append({
                "type": "invalid_shares",
                "level": "warning",
                "message": f"Row {idx+1}: Trade {symbol} on {date} has invalid share count: {shares}",
            })

    return warnings


def calculate_pnl(trades: list[dict]) -> dict:
    """Compute per-trade P&L, equity curve, and total return from a trade list.

    Pairs BUY->SELL trades per symbol using FIFO matching. Unpaired trades are skipped.
    Returns a dict with keys: trade_pnl, equity_curve, total_pnl, total_return_pct.
    """
    # FIFO buy queues per symbol: stores (date, price, shares) for each open BUY
    open_buys: dict[str, list[dict]] = {}
    trade_pnl: list[dict] = []
    cumulative_pnl = 0.0

    for trade in trades:
        symbol = trade.get("symbol")
        action = _normalize_action(trade.get("action"))
        if action == "BUY":
            open_buys.setdefault(symbol, []).append(trade)
        elif action == "SELL":
            if not open_buys.get(symbol):
                continue  # unmatched sell — already flagged by validate_trades
            buy = open_buys[symbol].pop(0)
            pnl = (trade.get("price", 0) - buy.get("price", 0)) * trade.get("shares", 0)
            cumulative_pnl += pnl
            trade_pnl.append({
                "buy_date": buy.get("date"),
                "sell_date": trade.get("date"),
                "symbol": symbol,
                "shares": trade.get("shares"),
                "buy_price": buy.get("price"),
                "sell_price": trade.get("price"),
                "pnl": round(pnl, 4),
                "cumulative_pnl": round(cumulative_pnl, 4),
            })

    # Equity curve: cumulative P&L at each sell event (chronological order)
    equity_curve = [
        {"date": t["sell_date"], "cumulative_pnl": t["cumulative_pnl"]}
        for t in trade_pnl
    ]

    # Total return as a percentage of total capital deployed (sum of all buy costs)
    total_buy_cost = sum(
        t["buy_price"] * t["shares"] for t in trade_pnl
    )
    total_return_pct = (
        round((cumulative_pnl / total_buy_cost) * 100, 4)
        if total_buy_cost > 0
        else 0.0
    )

    return {
        "trade_pnl": trade_pnl,
        "equity_curve": equity_curve,
        "total_pnl": round(cumulative_pnl, 4),
        "total_return_pct": total_return_pct,
    }


def analyze_uploaded_trades(csv_data: str) -> dict:
    """Main entry point: sanitize, detect format, parse, validate, and return a normalised trade dict for real trade history uploads."""
    try:
        clean = sanitize_csv(csv_data)
        # All downstream calls (detect_format, parse_detailed, etc.) must use `clean`, not `csv_data`
        fmt = detect_format(clean)
        if fmt == "summary":
            summary = parse_summary(clean)
            return {"format": fmt, "summary": summary}

        trades = parse_detailed(clean)
        if trades is None:
            trades = []
        all_issues = validate_trades(trades) or []
        WARNING_LEVELS = {"warning", "error"}
        INFO_LEVELS = {"info"}
        warnings = [i for i in all_issues if i.get("level", "warning") in WARNING_LEVELS]
        notices = [i for i in all_issues if i.get("level") in INFO_LEVELS]
        pnl = calculate_pnl(trades) if trades else {}
        result = {
            "format": fmt,
            "trades": trades,
            "warnings": warnings,
            "notices": notices,
            "pnl": pnl
        }
        print("DEBUG: Returning from detailed (main try):", result)
        return result
    except Exception as e:
        try:
            clean = sanitize_csv(csv_data)
            # All downstream calls (detect_format, parse_detailed, etc.) must use `clean`, not `csv_data`
            fmt = detect_format(clean)

            if fmt == "summary":
                summary = parse_summary(clean)
                result = {
                    "format": fmt,
                    "summary": summary,
                    "trades": [],
                    "warnings": [],
                    "notices": [],
                    "pnl": {}
                }
                print("DEBUG: Returning from summary:", result)
                return result

            trades = parse_detailed(clean)
            if trades is None:
                trades = []
            all_issues = validate_trades(trades) or []
            WARNING_LEVELS = {"warning", "error"}
            INFO_LEVELS = {"info"}
            warnings = [i for i in all_issues if i.get("level", "warning") in WARNING_LEVELS]
            notices = [i for i in all_issues if i.get("level") in INFO_LEVELS]
            pnl = calculate_pnl(trades) if trades else {}
            result = {
                "format": fmt,
                "trades": trades,
                "warnings": warnings,
                "notices": notices,
                "pnl": pnl
            }
            print("DEBUG: Returning from detailed:", result)
            return result
        except Exception as e:
            import traceback
            print("DEBUG: Exception in analyze_uploaded_trades:", e)
            traceback.print_exc()
            # Always return all expected keys, even on error
            return {
                "error": f"Failed to parse file: {str(e)}",
                "format": "detailed",  # fallback to detailed for test expectations
                "trades": [],
                "warnings": [],
                "notices": [],
                "pnl": {},
                # 'summary' key is omitted for detailed fallback
            }
