from agents.context_assembler import UserFinancialContextAssembler
from agents.contracts import ContextRequirement, FULL_DECISION_CONTEXT


def _seed(fake_db):
    fake_db.tables["users"] = [
        {
            "user_id": "alice", "email": "alice@example.com", "name": "Alice", "phone": "9999999999",
            "password_hash": "secret-hash", "monthly_income": 100000, "monthly_expenses": 30000,
            "primary_goal": "home", "risk_profile": "moderate", "updated_at": "2026-08-01T00:00:00+00:00",
        },
        {
            "user_id": "bob", "email": "bob@example.com", "password_hash": "bob-secret",
            "monthly_income": 1, "monthly_expenses": 1, "updated_at": "2026-08-02T00:00:00+00:00",
        },
    ]
    fake_db.tables["goals"] = [
        {"goal_id": "goal-a", "user_id": "alice", "goal_name": "Home", "target_amount": 5000000, "current_saved": 500000, "target_date": "2030-01-01"},
        {"goal_id": "goal-b", "user_id": "bob", "goal_name": "Private", "target_amount": 1, "current_saved": 0},
    ]
    fake_db.tables["bank_transactions"] = [
        {"bank_tx_id": "tx-a", "user_id": "alice", "tx_date": "2026-08-01", "description": "Sensitive merchant", "amount": 1000, "tx_type": "debit", "category": "food"}
    ]


def test_context_is_user_scoped_minimized_and_stably_versioned(fake_db):
    _seed(fake_db)
    assembler = UserFinancialContextAssembler(fake_db)
    requirement = ContextRequirement(required_sections={"profile", "goals", "cashflow"})

    first = assembler.assemble("alice", requirement)
    second = assembler.assemble("alice", requirement)

    serialized = first.model_dump(mode="json")
    assert first.context_version == second.context_version
    assert set(first.sections) == {"profile", "goals", "cashflow"}
    assert "alice@example.com" not in str(serialized)
    assert "secret-hash" not in str(serialized)
    assert "Sensitive merchant" not in str(serialized)
    assert "Private" not in str(serialized)
    assert all(item.evidence_id.startswith("private:") for item in first.evidence)
    assert first.data_as_of.isoformat() == "2026-08-01T00:00:00+00:00"


def test_financial_action_expands_requirements_and_reports_blockers(fake_db):
    _seed(fake_db)
    requirement = ContextRequirement(required_sections={"holdings"}, financial_action=True)

    snapshot = UserFinancialContextAssembler(fake_db).assemble("alice", requirement)

    assert FULL_DECISION_CONTEXT.issubset(requirement.required_sections)
    assert "missing_risk" in snapshot.missing_context_codes
    assert "decision_context_incomplete:missing_risk" in snapshot.blockers
    assert "conversation" not in snapshot.sections


def test_context_compaction_is_deterministic_and_dependency_free(fake_db):
    _seed(fake_db)
    fake_db.tables["goals"] = [
        {"goal_id": f"goal-{index:03}", "user_id": "alice", "goal_name": "X" * 300, "target_amount": index}
        for index in range(30)
    ]
    requirement = ContextRequirement(required_sections={"goals"}, max_serialized_chars=1000)
    assembler = UserFinancialContextAssembler(fake_db)

    first = assembler.assemble("alice", requirement)
    second = assembler.assemble("alice", requirement)

    assert first.compacted is True
    assert first.sections == second.sections
    assert first.context_version == second.context_version
    assert len(first.evidence) == len(first.sections["goals"])
