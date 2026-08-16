"""Exercise LLM import mapping with synthetic unfamiliar provider formats."""
from __future__ import annotations

from services.import_mapping_service import suggest_import_mapping


CASES = {
    "unknown_equity_broker.csv": (
        "Execution Day,Security Identifier,Instrument Label,Order Direction,Executed Units,Trade Rate,Venue\n"
        "12/08/2026,ABC123,Example Industries,Purchase,5,120.50,NSE\n"
        "13/08/2026,XYZ789,Example Systems,Sale,2,88.10,BSE\n"
    ),
    "regional_bank_export.csv": (
        "Posting Day,Details,Money Out,Money In,Ledger Total,Reference\n"
        "12/08/2026,Card purchase,450,,12550,R001\n"
        "13/08/2026,Transfer received,,5000,17550,R002\n"
    ),
    "small_broker_positions.csv": (
        "Instrument Code,Security Description,Net Units,Acquisition Average,Last Traded\n"
        "ABC,Example Industries,15,105.20,121.00\n"
        "XYZ,Example Systems,8,75.00,89.50\n"
    ),
    "fund_platform_activity.csv": (
        "Processed On,Portfolio Scheme,Activity,Allotted Units,Applicable NAV,Folio\n"
        "12/08/2026,Example Flexi Cap,SIP,25.5,48.20,F001\n"
        "13/08/2026,Example Small Cap,Redemption,5,62.10,F002\n"
    ),
}


def main() -> None:
    for filename, text in CASES.items():
        content = text.encode()
        headers = text.splitlines()[0].split(",")
        print(filename, suggest_import_mapping(headers, filename, content))


if __name__ == "__main__":
    main()
