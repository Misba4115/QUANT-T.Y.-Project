from services.conversation_memory import ConversationMemoryService


def test_conversation_summary_is_private_versioned_and_idempotently_updated(fake_db):
    messages = [{"role":"user" if i % 2 == 0 else "assistant", "content":f"Message {i}"} for i in range(12)]
    service = ConversationMemoryService(fake_db)
    first = service.update("alice", "conversation-a", messages)
    second = service.update("alice", "conversation-a", [*messages, {"role":"user","content":"More"}])
    assert first["summary_version"] == "conversation-summary-v1"
    assert second["summary_id"] == first["summary_id"]
    assert second["message_count"] == 13
    assert len(fake_db.tables["conversation_summaries"]) == 1
    assert fake_db.tables["conversation_summaries"][0]["user_id"] == "alice"
