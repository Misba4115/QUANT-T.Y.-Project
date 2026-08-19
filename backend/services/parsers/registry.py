"""Advertise only parser families backed by current passing fixtures."""
from __future__ import annotations


PARSER_CAPABILITIES = (
    {"format_id":"generic-tabular-v1","extensions":[".csv",".xlsx"],"document_families":["bank_transactions","broker_holdings","broker_tradebook","mutual_fund_holdings","sip_transactions","etf_holdings"],"status":"partial","reason_code":"generic_headers_fixture_verified","source_examples":["Zerodha","Groww","Upstox","Angel One","ICICI Direct","HDFC Securities","Kotak Securities"]},
    {"format_id":"text-cas-v1","extensions":[".pdf"],"document_families":["cams_kfintech_text_cas","nsdl_cdsl_text_cas"],"status":"partial","reason_code":"text_only_no_ocr","source_examples":["CAMS","KFintech","NSDL","CDSL"]},
)


def parser_capability_matrix() -> dict:
    return {
        "capabilities": list(PARSER_CAPABILITIES),
        "ocr": {"status":"not_configured","low_confidence_auto_commit":False},
        "unknown_layout_policy":"reject_with_actionable_reason",
    }
