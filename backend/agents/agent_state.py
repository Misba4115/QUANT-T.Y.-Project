from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    request_id: str
    user_id: str
    conversation_id: str
    user_message: str
    history: list[dict[str, str]]
    intent: str
    route_decision: dict[str, Any]
    selected_agents: list[str]
    completed_nodes: list[str]
    agent_outputs: dict[str, Any]
    public_sources: list[dict[str, Any]]
    response: str
    warnings: list[str]
    errors: list[dict[str, str]]
    run_trace: list[dict[str, Any]]
    financial_context: dict[str, Any]
