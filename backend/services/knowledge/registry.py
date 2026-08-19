"""Allowlisted authoritative discovery seeds and database registry access."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


OFFICIAL_DOMAINS = frozenset({
    "incometax.gov.in", "www.incometax.gov.in", "incometaxindia.gov.in", "www.incometaxindia.gov.in",
    "sebi.gov.in", "www.sebi.gov.in", "rbi.org.in", "www.rbi.org.in", "egazette.nic.in", "www.egazette.nic.in",
    "amfiindia.com", "www.amfiindia.com",
})


@dataclass(frozen=True)
class KnowledgeSeed:
    source_id: str
    authority: str
    listing_url: str
    document_family: str
    topic_tags: tuple[str, ...]
    expected_content_types: tuple[str, ...] = ("text/html", "application/pdf")
    review_required: bool = True


DEFAULT_SEEDS = (
    KnowledgeSeed("income-tax-act-2025", "Income Tax Department", "https://www.incometax.gov.in/iec/foportal/newdownloads/income-tax-act-2025", "act_and_guidance", ("tax",)),
    KnowledgeSeed("sebi-master-circulars", "SEBI", "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=6", "master_circular", ("securities", "investor_protection")),
    KnowledgeSeed("rbi-master-directions", "RBI", "https://www.rbi.org.in/scripts/BS_ViewMasterDirections.aspx?did=339", "master_direction", ("banking", "payments")),
)


def validate_official_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in OFFICIAL_DOMAINS or parsed.username or parsed.password:
        raise ValueError("Knowledge URL is not an allowlisted official HTTPS origin")


def seed_registry(db) -> list[dict]:
    rows = []
    for seed in DEFAULT_SEEDS:
        validate_official_url(seed.listing_url)
        payload = {
            "source_id": seed.source_id, "authority": seed.authority, "official_domain": urlparse(seed.listing_url).hostname,
            "listing_url": seed.listing_url, "document_family": seed.document_family,
            "topic_tags": list(seed.topic_tags), "jurisdiction": "IN", "discovery_schedule": "P1D",
            "expected_content_types": list(seed.expected_content_types), "review_required": seed.review_required,
            "status": "active",
        }
        existing = db.table("knowledge_sources").select("*").eq("source_id", seed.source_id).limit(1).execute().data or []
        rows.append((db.table("knowledge_sources").update(payload).eq("source_id", seed.source_id) if existing else db.table("knowledge_sources").insert(payload)).execute().data[0])
    return rows
