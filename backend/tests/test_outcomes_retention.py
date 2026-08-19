from datetime import datetime, timedelta, timezone

from services.inbox_ingestion import MemoryBlobStore
from services.outcome_evaluator import OutcomeEvaluator
from services.retention import RetentionCleanupService


def test_outcome_evaluator_never_auto_mutates_and_requires_sample_gate():
    rows = [{"predicted": index, "realized": index + 1} for index in range(30)]
    result = OutcomeEvaluator().evaluate(rows, target_version="goal-v1")
    assert result["status"] == "review_required"
    assert result["automatic_mutation"] is False
    assert result["calibration_proposal"]["requires_approval"] is True


def test_retention_deletes_due_blob_and_is_idempotent(fake_db):
    store = MemoryBlobStore(); store.put("alice/message/file", b"encrypted")
    fake_db.tables["ingestion_messages"] = [{"ingestion_message_id":"m1","user_id":"alice","storage_key":"alice/message/file","purge_after":(datetime.now(timezone.utc)-timedelta(days=1)).isoformat()}]
    service = RetentionCleanupService(fake_db, store)
    first, second = service.run(), service.run()
    assert first["deleted"] == 1 and second["deleted"] == 0
    assert store.values == {}
    assert first["attempts"][0]["object_key_hash"] != "alice/message/file"
