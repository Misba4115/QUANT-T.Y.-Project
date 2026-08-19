"""Bounded coordinator for parallel specialists and typed follow-up requests."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from time import monotonic
from typing import Any, Callable

from agents.contracts import AgentRequest, RunTraceEvent


Runner = Callable[[str, Any], dict[str, Any]]


class AgentCoordinator:
    def __init__(
        self,
        db: Any,
        runners: dict[str, Runner],
        *,
        max_follow_up_rounds: int = 2,
        per_agent_timeout_seconds: float = 10,
        global_timeout_seconds: float = 25,
    ):
        self.db = db
        self.runners = runners
        self.max_follow_up_rounds = max(0, min(max_follow_up_rounds, 2))
        self.per_agent_timeout_seconds = per_agent_timeout_seconds
        self.global_timeout_seconds = global_timeout_seconds

    def execute(self, user_id: str, specialists: list[str]) -> tuple[dict[str, dict], list[dict], list[dict]]:
        started = monotonic()
        outputs: dict[str, dict] = {}
        errors: list[dict] = []
        trace: list[RunTraceEvent] = []
        requested = list(dict.fromkeys(name for name in specialists if name in self.runners))
        attempted: set[str] = set()
        seen_requests: set[tuple[str, str, tuple[str, ...], str | None]] = set()

        for round_number in range(self.max_follow_up_rounds + 1):
            pending = [name for name in requested if name not in attempted]
            if not pending or monotonic() - started >= self.global_timeout_seconds:
                break
            attempted.update(pending)
            with ThreadPoolExecutor(max_workers=len(pending), thread_name_prefix="quant-agent") as pool:
                future_map = {pool.submit(self.runners[name], user_id, self.db): name for name in pending}
                try:
                    for future in as_completed(
                        future_map,
                        timeout=min(self.global_timeout_seconds - (monotonic() - started), self.per_agent_timeout_seconds),
                    ):
                        name = future_map[future]
                        try:
                            output = future.result(timeout=0)
                            outputs[name] = output
                            trace.append(RunTraceEvent(sequence=len(trace), event="agent_completed", capability=name, status=str(output.get("status", "available"))))
                            if round_number < self.max_follow_up_rounds:
                                for raw in output.get("requests", []):
                                    request = AgentRequest.model_validate(raw)
                                    key = (request.requesting_agent, request.requested_capability, tuple(request.required_fields), request.parent_claim_id)
                                    if key in seen_requests:
                                        continue
                                    seen_requests.add(key)
                                    if request.requesting_agent == request.requested_capability:
                                        errors.append({"node": name, "code": "recursive_self_request"})
                                    elif request.requested_capability not in self.runners:
                                        errors.append({"node": name, "code": "capability_not_allowed"})
                                    else:
                                        requested.append(request.requested_capability)
                                        trace.append(RunTraceEvent(sequence=len(trace), event="follow_up_authorized", capability=request.requested_capability, status="scheduled"))
                        except Exception as exc:
                            errors.append({"node": name, "code": type(exc).__name__})
                            trace.append(RunTraceEvent(sequence=len(trace), event="agent_failed", capability=name, status="failed", detail=type(exc).__name__))
                except TimeoutError:
                    for future, name in future_map.items():
                        if not future.done():
                            future.cancel()
                            errors.append({"node": name, "code": "agent_timeout"})
                            trace.append(RunTraceEvent(sequence=len(trace), event="agent_timeout", capability=name, status="failed"))
            requested = list(dict.fromkeys(requested))

        if monotonic() - started >= self.global_timeout_seconds:
            trace.append(RunTraceEvent(sequence=len(trace), event="global_timeout", status="partial"))
        return outputs, errors, [item.model_dump(mode="json") for item in trace]
