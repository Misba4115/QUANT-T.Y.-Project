"""Best-effort CAMS/KFintech CAS text parser with explicit failure modes."""
from __future__ import annotations

import io
import re

import pdfplumber


FOLIO_RE = re.compile(r"Folio\s*(?:No\.?|Number)?\s*[:\-]?\s*([A-Z0-9/\-]+)", re.I)
DETAIL_RE = re.compile(
    r"Units?\s*[:\-]?\s*([\d,]+(?:\.\d+)?)\s+"
    r"(?:NAV|Average\s+NAV)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d+)?)",
    re.I,
)


def parse_cas_pdf(file_bytes: bytes) -> list[dict]:
    try:
        pdf = pdfplumber.open(io.BytesIO(file_bytes))
    except Exception as exc:
        message = str(exc).lower()
        if "password" in message or "encrypt" in message:
            raise ValueError("The CAS PDF is encrypted; export an unlocked copy before upload") from exc
        raise ValueError("The uploaded file is not a readable PDF") from exc

    with pdf:
        page_text = [page.extract_text() or "" for page in pdf.pages]
    text = "\n".join(page_text).strip()
    if not text:
        raise ValueError("No selectable text was found; scanned CAS PDFs require OCR before upload")

    holdings: list[dict] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    current_folio: str | None = None
    current_scheme: str | None = None
    for line in lines:
        folio_match = FOLIO_RE.search(line)
        if folio_match:
            current_folio = folio_match.group(1)
            continue
        lowered = line.lower()
        if any(word in lowered for word in ("fund", "scheme", "plan")) and not DETAIL_RE.search(line):
            current_scheme = re.sub(r"^Scheme\s*[:\-]?\s*", "", line, flags=re.I)[:240]
        detail = DETAIL_RE.search(line)
        if detail and current_scheme:
            units = float(detail.group(1).replace(",", ""))
            nav = float(detail.group(2).replace(",", ""))
            holdings.append(
                {
                    "mf_name": current_scheme,
                    "units": units,
                    "avg_nav": nav,
                    "folio_number": current_folio,
                }
            )
    if not holdings:
        raise ValueError("This CAS layout is not yet recognized; upload the CSV export or a supported CAMS/KFintech text PDF")
    return holdings
