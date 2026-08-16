"""A small in-memory PostgREST/Supabase test double."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from repositories.base import TABLES


@dataclass
class FakeResult:
    data: list[dict[str, Any]]


class FakeQuery:
    def __init__(self, client: "FakeSupabase", table: str):
        self.client = client
        self.table_name = table
        self.operation = "select"
        self.payload: Any = None
        self.filters: list[tuple[str, Any]] = []
        self.ordering: tuple[str, bool] | None = None
        self.row_limit: int | None = None

    def select(self, _columns: str = "*") -> "FakeQuery":
        self.operation = "select"
        return self

    def insert(self, payload: dict | list[dict]) -> "FakeQuery":
        self.operation = "insert"
        self.payload = payload
        return self

    def upsert(self, payload: dict | list[dict], **_kwargs) -> "FakeQuery":
        self.operation = "upsert"
        self.payload = payload
        return self

    def update(self, payload: dict) -> "FakeQuery":
        self.operation = "update"
        self.payload = payload
        return self

    def delete(self) -> "FakeQuery":
        self.operation = "delete"
        return self

    def eq(self, field: str, value: Any) -> "FakeQuery":
        self.filters.append((field, value))
        return self

    def order(self, field: str, desc: bool = False, **_kwargs) -> "FakeQuery":
        self.ordering = (field, desc)
        return self

    def limit(self, value: int) -> "FakeQuery":
        self.row_limit = value
        return self

    def _matches(self, row: dict[str, Any]) -> bool:
        return all(str(row.get(field)) == str(value) for field, value in self.filters)

    def _prepare(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = deepcopy(payload)
        spec = TABLES.get(self.table_name)
        if spec:
            row.setdefault(spec.id_field, str(uuid4()))
        now = datetime.now(timezone.utc).isoformat()
        row.setdefault("created_at", now)
        if self.table_name in {
            "users", "banking_accounts", "equity_holdings", "mutual_fund_holdings",
            "etf_holdings", "crypto_holdings", "goals", "chat_conversations",
        }:
            row.setdefault("updated_at", now)
        return row

    def execute(self) -> FakeResult:
        rows = self.client.tables.setdefault(self.table_name, [])
        if self.operation == "select":
            selected = [deepcopy(row) for row in rows if self._matches(row)]
            if self.ordering:
                field, desc = self.ordering
                selected.sort(key=lambda row: str(row.get(field) or ""), reverse=desc)
            if self.row_limit is not None:
                selected = selected[: self.row_limit]
            return FakeResult(selected)

        if self.operation in {"insert", "upsert"}:
            payloads = self.payload if isinstance(self.payload, list) else [self.payload]
            created: list[dict[str, Any]] = []
            for payload in payloads:
                row = self._prepare(payload)
                if self.operation == "upsert":
                    spec = TABLES.get(self.table_name)
                    match = None
                    if spec and row.get(spec.id_field):
                        match = next((item for item in rows if item.get(spec.id_field) == row[spec.id_field]), None)
                    if match:
                        match.update(row)
                        created.append(deepcopy(match))
                        continue
                rows.append(row)
                created.append(deepcopy(row))
            return FakeResult(created)

        matched = [row for row in rows if self._matches(row)]
        if self.operation == "update":
            for row in matched:
                row.update(deepcopy(self.payload))
                if "updated_at" in row:
                    row["updated_at"] = datetime.now(timezone.utc).isoformat()
            return FakeResult(deepcopy(matched))
        if self.operation == "delete":
            deleted = deepcopy(matched)
            self.client.tables[self.table_name] = [row for row in rows if not self._matches(row)]
            return FakeResult(deleted)
        raise AssertionError(f"Unsupported fake operation: {self.operation}")


class FakeRPC:
    def __init__(self, client: "FakeSupabase", name: str, params: dict[str, Any]):
        self.client = client
        self.name = name
        self.params = params

    def execute(self) -> FakeResult:
        handler = self.client.rpc_handlers.get(self.name)
        return FakeResult(handler(self.params) if handler else [])


class FakeSupabase:
    def __init__(self):
        self.tables: dict[str, list[dict[str, Any]]] = {}
        self.rpc_handlers: dict[str, Any] = {}

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(self, name)

    def rpc(self, name: str, params: dict[str, Any] | None = None) -> FakeRPC:
        return FakeRPC(self, name, params or {})

    def reset(self) -> None:
        self.tables.clear()
        self.rpc_handlers.clear()
