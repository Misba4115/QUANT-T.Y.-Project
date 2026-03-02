"""
CAS PDF Parser — Parse CAMS/KFintech Consolidated Account Statement PDFs
"""
# import pdfplumber
# import re


def parse_cas_pdf(file_bytes: bytes) -> list[dict]:
    """
    Extract mutual fund holdings from a CAS PDF (CAMS or KFintech format).

    Steps:
      1. Open PDF with pdfplumber (in-memory from bytes)
      2. Extract text page by page
      3. Use regex to identify fund names, folio numbers, units, NAV, value
         Common patterns:
           - Folio No: <XXXXXXX>
           - Scheme: <Fund Name>
           - Units: <float> | NAV: <float> | Value: <float>
      4. Clean and return list of dicts matching mutual_fund_holdings schema

    Expected output per holding:
        {
            "name": "SBI Bluechip Fund Direct Growth",
            "folio_number": "1234567/89",
            "units": 150.234,
            "avg_nav": 65.43,
            "current_nav": 72.10,
            "current_value": 10831.91
        }

    Note: CAS formats differ between CAMS and KFintech. Start with CAMS.
    TODO: implement
    """
    raise NotImplementedError
