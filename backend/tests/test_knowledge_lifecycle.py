from services.knowledge.lifecycle import KnowledgeLifecycle
from services.knowledge.registry import seed_registry, validate_official_url


class Indexer:
    def __init__(self): self.events = []
    def stage(self, version): self.events.append(("stage", version["knowledge_version_id"]))
    def promote(self, version_id): self.events.append(("promote", version_id))
    def rollback(self, version_id): self.events.append(("rollback", version_id))


def test_registry_rejects_non_official_origins_and_seeds_idempotently(fake_db):
    try:
        validate_official_url("https://evil.example/sebi.pdf")
        assert False
    except ValueError:
        pass
    assert len(seed_registry(fake_db)) == 3
    assert len(seed_registry(fake_db)) == 3
    assert len(fake_db.tables["knowledge_sources"]) == 3


def test_stage_is_hashed_idempotent_and_changed_content_has_reviewable_diff(fake_db):
    seed_registry(fake_db)
    content = [b"<h1>Official rule v1</h1>", b"<h1>Official rule v2 material change</h1>"]
    lifecycle = KnowledgeLifecycle(fake_db, fetch=lambda url: (content.pop(0), "text/html", url))
    url = "https://www.sebi.gov.in/legal.html"
    first = lifecycle.stage("sebi-master-circulars", url, title="Rules")
    duplicate = KnowledgeLifecycle(fake_db, fetch=lambda _url: (b"<h1>Official rule v1</h1>", "text/html", url)).stage("sebi-master-circulars", url, title="Rules")
    changed = lifecycle.stage("sebi-master-circulars", url, title="Rules")
    assert first["status"] == "staged" and duplicate["idempotent"] is True
    assert changed["diff_text"] and changed["idempotent"] is False
    assert len(fake_db.tables["knowledge_reviews"]) == 2


def test_rejected_or_pending_document_cannot_publish_and_approved_can_rollback(fake_db):
    seed_registry(fake_db)
    url = "https://www.rbi.org.in/rules"
    indexer = Indexer()
    lifecycle = KnowledgeLifecycle(fake_db, fetch=lambda _url: (b"Official direction", "text/plain", url), indexer=indexer)
    version = lifecycle.stage("rbi-master-directions", url, title="Direction")
    try:
        lifecycle.publish(version["knowledge_version_id"], "reviewer")
        assert False
    except ValueError:
        pass
    fake_db.tables["knowledge_reviews"][0]["status"] = "approved"
    assert lifecycle.publish(version["knowledge_version_id"], "reviewer")["status"] == "active"
    assert lifecycle.rollback(version["knowledge_version_id"])["rolled_back"] is True
    assert [event[0] for event in indexer.events] == ["stage", "promote", "rollback"]
