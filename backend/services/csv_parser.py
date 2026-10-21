"""CSV normalization helpers for broker and native QUANT exports."""
from __future__ import annotations

import csv
import io
from typing import Any


ALIASES = {
    # Securities and broker exports
    "stock_symbol": "symbol",
    "tradingsymbol": "symbol",
    "instrument": "symbol",
    "ticker": "symbol",
    "scrip": "symbol",
    "company_name": "equity_name",
    "security_name": "asset_name",
    "average_price": "avg_price",
    "average_buy_price": "avg_price",
    "avg_cost": "avg_price",
    "qty": "quantity",
    "available_quantity": "quantity",
    "shares": "quantity",
    "last_price": "current_price",
    "last_traded_price": "current_price",
    "market_price": "current_price",
    "price_per_unit": "price",
    "unit_price": "price",
    "trade_price": "price",
    "fees_commission": "fees",
    "commission": "fees",
    "brokerage_charges": "fees",
    # Mutual funds and ETFs
    "scheme_name": "mf_name",
    "fund_name": "mf_name",
    "scheme": "mf_name",
    "average_nav": "avg_nav",
    "purchase_nav": "avg_nav",
    "nav": "current_nav",
    "folio": "folio_number",
    "etf": "etf_name",
    "etf_fund_name": "etf_name",
    # Bank accounts
    "bank_name": "institution",
    "account_no": "account_number",
    "account_balance": "current_balance",
    "balance": "current_balance",
    "primary_account": "is_primary",
    # Crypto
    "coin_name": "crypto_name",
    "token_name": "crypto_name",
    "crypto_exchange": "exchange",
    "wallet": "wallet_address",
    # Goals
    "goal": "goal_name",
    "target": "target_amount",
    "saved_amount": "current_saved",
    "deadline": "target_date",
    # Transactions
    "transactionid": "transaction_id",
    "assettype": "asset_type",
    "assetname": "asset_name",
    "transactiontype": "tx_type",
    "date": "tx_date",
    "transaction_date": "tx_date",
    "value_date": "tx_date",
    "transaction_datetime": "occurred_at",
    "transaction_timestamp": "occurred_at",
    "timestamp": "occurred_at",
    "narration": "description",
    "remarks": "description",
    "transaction_description": "description",
    "transaction_amount": "amount",
    "transaction_type": "tx_type",
    "withdrawal_amt": "debit",
    "withdrawal_amount": "debit",
    "deposit_amt": "credit",
    "deposit_amount": "credit",
}


def normalize_header(value: Any) -> str:
    key = str(value or "").strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")
    while "__" in key:
        key = key.replace("__", "_")
    return ALIASES.get(key, key)


def header_mapping(fieldnames: list[Any], overrides: dict[str, str] | None = None) -> dict[str, str]:
    """Return every source header and the canonical header used by QUANT."""
    overrides = overrides or {}
    return {
        str(value or "").strip(): overrides.get(str(value or "").strip(), normalize_header(value))
        for value in fieldnames
        if str(value or "").strip()
    }


def parse_csv_document(
    file_bytes: bytes,
    overrides: dict[str, str] | None = None,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Parse rows while preserving an auditable source-to-canonical header map."""
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = file_bytes.decode("cp1252")
        except UnicodeDecodeError as exc:
            raise ValueError("CSV encoding is not UTF-8 or Windows-1252") from exc
    matrix = _parse_delimited_matrix(text)
    if not matrix or not matrix[0]:
        raise ValueError("CSV has no header row")
    fieldnames = matrix[0]
    mapping = header_mapping(fieldnames, overrides)
    rows: list[dict[str, str]] = []
    for values in matrix[1:]:
        raw = {
            fieldnames[index]: value
            for index, value in enumerate(values)
            if index < len(fieldnames)
        }
        normalized = {
            mapping.get(str(key).strip(), normalize_header(key)): str(value or "").strip()
            for key, value in raw.items()
            if key is not None
        }
        if any(value for value in normalized.values()):
            rows.append(normalized)
    return rows, mapping


def _parse_delimited_matrix(text: str, allow_outer_unwrap: bool = True) -> list[list[str]]:
    """Detect common delimiters and recover exports that quote every entire row."""
    candidates = [",", ";", "\t", "|"]
    best_rows: list[list[str]] = []
    best_score = (0, 0)
    for delimiter in candidates:
        try:
            parsed = list(csv.reader(io.StringIO(text), delimiter=delimiter))
        except csv.Error:
            continue
        nonempty = [row for row in parsed if any(str(value).strip() for value in row)]
        if not nonempty:
            continue
        widths = [len(row) for row in nonempty[:50]]
        common_width = max(set(widths), key=widths.count)
        consistent = sum(width == common_width for width in widths)
        score = (common_width, consistent)
        if common_width > 1 and score > best_score:
            best_rows, best_score = nonempty, score
    if best_rows:
        return best_rows

    outer_rows = list(csv.reader(io.StringIO(text)))
    nonempty_outer = [row for row in outer_rows if any(str(value).strip() for value in row)]
    if (
        allow_outer_unwrap
        and nonempty_outer
        and all(len(row) == 1 for row in nonempty_outer)
        and any(delimiter in nonempty_outer[0][0] for delimiter in candidates)
    ):
        unwrapped = "\n".join(row[0] for row in nonempty_outer)
        return _parse_delimited_matrix(unwrapped, allow_outer_unwrap=False)
    return nonempty_outer


def parse_csv_rows(file_bytes: bytes) -> list[dict[str, str]]:
    rows, _mapping = parse_csv_document(file_bytes)
    return rows


def parse_equity_csv(file_bytes: bytes, broker: str = "auto") -> list[dict[str, Any]]:
    rows = parse_csv_rows(file_bytes)
    output: list[dict[str, Any]] = []
    for row in rows:
        symbol = row.get("symbol", "").upper()
        if not symbol:
            raise ValueError("Equity CSV contains a row without a symbol")
        output.append(
            {
                "symbol": symbol,
                "equity_name": row.get("equity_name") or symbol,
                "exchange": (row.get("exchange") or "NSE").upper(),
                "quantity": float(str(row.get("quantity", "0")).replace(",", "")),
                "avg_price": float(str(row.get("avg_price", "0")).replace(",", "")),
                "broker": row.get("broker") or (None if broker == "auto" else broker),
                "demat_account": row.get("demat_account") or None,
                "current_price": float(str(row["current_price"]).replace(",", "")) if row.get("current_price") else None,
            }
        )
    return output
