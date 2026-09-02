"""LangGraph manager with independent specialist-agent nodes."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from langgraph.graph import END, StateGraph

from agents.agent_state import AgentState
from agents.cashflow import run_cashflow_agent
from agents.coordinator import AgentCoordinator
from agents.context_assembler import UserFinancialContextAssembler
from agents.contracts import ContextRequirement
from agents.guardian import run_guardian
from agents.intent_router import StructuredIntentRouter
from agents.response_grounding import validate_material_numbers
from agents.portfolio import run_portfolio_agent
from agents.tax import run_tax_agent
from services.llm_service import generate_chat_response
from services.qdrant_rag_service import PublicKnowledgeService

CITATION_RE = re.compile(r"\[((?:private|public):[^\]]+)\]")


class ChatOrchestrator:
    def __init__(
        self,
        db: Any,
        *,
        llm: Callable[[list[dict[str, str]]], str] = generate_chat_response,
        public_rag: Any | None = None,
        intent_router: StructuredIntentRouter | None = None,
        runners: dict[str, Callable[[str, Any], dict]] | None = None,
    ):
        self.db = db
        self.llm = llm
        self.public_rag = public_rag
        self.intent_router = intent_router or StructuredIntentRouter()
        self.runners = runners or {
            "guardian": run_guardian,
            "portfolio": run_portfolio_agent,
            "tax": run_tax_agent,
            "cashflow": run_cashflow_agent,
        }
        self.coordinator = AgentCoordinator(db, self.runners)
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("manager", self._manager)
        graph.add_node("coordinate", self._coordinate)
        graph.add_node("retrieve", self._retrieve)
        graph.add_node("generate", self._generate)
        graph.set_entry_point("manager")
        graph.add_conditional_edges(
            "manager",
            lambda state: "coordinate" if state["selected_agents"] else "retrieve",
            {"coordinate": "coordinate", "retrieve": "retrieve"},
        )
        graph.add_edge("coordinate", "retrieve")
        graph.add_edge("retrieve", "generate")
        graph.add_edge("generate", END)
        return graph.compile()

    def run(
        self,
        user_id: str,
        user_message: str,
        conversation_id: str,
        history: list[dict[str, str]] | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        result = self.graph.invoke(
            {
                "request_id": request_id or str(uuid4()),
                "user_id": user_id,
                "conversation_id": conversation_id,
                "user_message": user_message,
                "history": history or [],
                "selected_agents": [],
                "completed_nodes": [],
                "agent_outputs": {},
                "public_sources": [],
                "warnings": [],
                "errors": [],
                "run_trace": [],
                "financial_context": {},
            }
        )
        citations = result.get("public_sources", [])
        sections = [
            {
                "specialist": name,
                "status": str(output.get("status", "available")),
                "summary": self._specialist_summary(name, output),
                "metrics": {key: value for key, value in output.items() if key not in {"alerts", "assumptions", "requests", "agent"} and isinstance(value, (str, int, float, bool, type(None)))},
            }
            for name, output in result.get("agent_outputs", {}).items()
        ]
        limitations = list(result.get("financial_context", {}).get("blockers", []))
        limitations.extend(f"{item['node']}:{item['code']}" for item in result.get("errors", []))
        return {
            "reply": result["response"],
            "intent": result["intent"],
            "agent": "manager" if len(result["selected_agents"]) != 1 else result["selected_agents"][0],
            "selected_agents": result["selected_agents"],
            "completed_nodes": result["completed_nodes"],
            "citations": citations,
            "warnings": result.get("warnings", []),
            "errors": result.get("errors", []),
            "routing": result.get("route_decision", {}),
            "run_trace": result.get("run_trace", []),
            "routing_confidence": result.get("route_decision", {}).get("confidence"),
            "analysis_sections": sections,
            "evidence_summary": {
                "context_version": result.get("financial_context", {}).get("context_version"),
                "private_evidence_count": len(result.get("financial_context", {}).get("evidence", [])),
                "public_source_count": len(citations),
            },
            "limitations": limitations,
            "degraded_dependencies": sorted({item["node"] for item in result.get("errors", [])}),
            "data_as_of": datetime.now(timezone.utc).isoformat(),
        }

    def _manager(self, state: AgentState) -> dict:
        decision = self.intent_router.route(state["user_message"])
        selected = decision.required_specialists
        legacy_intent = "multi_agent" if len(selected) > 1 else selected[0] if selected else "general"
        try:
            snapshot = UserFinancialContextAssembler(self.db).assemble(
                state["user_id"],
                ContextRequirement(required_sections=decision.required_private_contexts, financial_action=decision.primary_intent == "recommendation_like"),
            ).model_dump(mode="json")
        except Exception as exc:
            snapshot = {"blockers": [f"context_unavailable:{type(exc).__name__}"], "evidence": []}
        return {
            "selected_agents": selected,
            "intent": legacy_intent,
            "route_decision": decision.model_dump(mode="json"),
            "financial_context": snapshot,
            "completed_nodes": [*state["completed_nodes"], "manager"],
        }

    def _coordinate(self, state: AgentState) -> dict:
        # Run specialist agents and public knowledge retrieval in parallel to cut overall latency.
        # Public retrieval is cheap I/O; we submit it as an additional future alongside the coordinator execution.
        selected_agents = state["selected_agents"]
        user_id = state["user_id"]
        public_rag_future = None
        # Prepare executor with one extra worker for public search if needed.
        from concurrent.futures import ThreadPoolExecutor, as_completed
        executor = ThreadPoolExecutor(max_workers=len(selected_agents) + 1)
        futures = {}
        # Specialist execution future
        futures[executor.submit(self.coordinator.execute, user_id, selected_agents)] = "specialists"
        # Public knowledge future (if RAG is configured)
        if state.get("route_decision", {}).get("requires_public_knowledge", state["intent"] in {"tax", "general", "multi_agent"}):
            def _search_public():
                try:
                    service = self.public_rag or PublicKnowledgeService()
                    return service.search(state["user_message"], limit=5)
                except Exception:
                    return []
            futures[executor.submit(_search_public)] = "public"

        outputs: dict = {}
        errors: list = []
        trace: list = []
        public_sources: list = []

        for future in as_completed(futures):
            kind = futures[future]
            if kind == "specialists":
                sp_outputs, sp_errors, sp_trace = future.result()
                outputs = sp_outputs
                errors = sp_errors
                trace = sp_trace
            elif kind == "public":
                public_sources = future.result()

        # Merge public sources into state for later retrieve step (skip duplicate retrieve).
        state["public_sources"] = public_sources
        completed = [*state["completed_nodes"], *[name for name in selected_agents if name in outputs]]
        return {"agent_outputs": outputs, "errors": [*state["errors"], *errors], "run_trace": trace, "completed_nodes": completed}

    def _retrieve(self, state: AgentState) -> dict:
        # If public sources were already fetched in parallel during coordination, reuse them.
        if state.get("public_sources"):
            return {
                "public_sources": state["public_sources"],
                "warnings": list(state["warnings"]),
                "completed_nodes": [*state["completed_nodes"], "retrieve"],
            }
        public_sources: list[dict] = []
        warnings = list(state["warnings"])
        if state.get("route_decision", {}).get("requires_public_knowledge", state["intent"] in {"tax", "general", "multi_agent"}):
            try:
                service = self.public_rag or PublicKnowledgeService()
                public_sources = service.search(state["user_message"], limit=5)
            except Exception as exc:
                warnings.append(f"Public knowledge search unavailable ({type(exc).__name__})")
        return {
            "public_sources": public_sources,
            "warnings": warnings,
            "completed_nodes": [*state["completed_nodes"], "retrieve"],
        }

    def _generate(self, state: AgentState) -> dict:
        route = state.get("route_decision", {})
        if route.get("primary_intent") == "unsupported":
            return {
                "response": "I can explain financial considerations and risks, but I cannot guarantee returns or execute a trade. I can help you review the relevant evidence and constraints instead.",
                "warnings": [*state["warnings"], "Unsupported financial action was not executed"],
                "completed_nodes": [*state["completed_nodes"], "generate"],
            }
        citations = state["public_sources"]
        source_text = "\n".join(
            f"[{item['citation_id']}] {item['title']} ({item.get('locator') or 'source'}): {item.get('excerpt') or ''}"
            for item in citations
        ) or "No retrieved source cleared the relevance/configuration gate."
        system = (
            "You are QUANT Financial Intelligence Copilot, an institutional-grade multi-agent financial platform for Indian retail investors.\n\n"
            "ARCHITECTURE & EVIDENCE CONTEXT:\n"
            "You synthesize deterministic analysis from 4 specialized engines (Portfolio Valuation, Section 80C & Capital Gains Tax, Banking Cashflow, and Guardian Anomaly Detector) and verified public financial knowledge.\n"
            "Always ground your response in the verified data provided below in MINIMIZED USER CONTEXT and SPECIALIST OUTPUTS.\n\n"
            "RESPONSE FORMAT & STRUCTURE:\n"
            "Structure every response cleanly, professionally, and systematically using markdown:\n\n"
            "### Direct Assessment\n"
            "[1 concise summary sentence answering the user's question directly.]\n\n"
            "### Key Financial Insights\n"
            "- **Portfolio & Cash Flow:** [Analysis of net worth, cash position, or monthly surplus]\n"
            "- **Tax & Section 80C:** [Remaining §80C tax-saving headroom or capital gains tax status]\n"
            "- **Risk & Allocation:** [Asset allocation, diversification, or risk observations]\n\n"
            "### Strategic Options\n"
            "1. **[Option 1 - e.g. ELSS / Tax Saver Fund]:** [1 concise sentence with rationale]\n"
            "2. **[Option 2 - e.g. Broad-Market Index Fund / Flexi-Cap]:** [1 concise sentence]\n"
            "3. **[Option 3 - e.g. Emergency / Liquid Buffer]:** [1 concise sentence]\n\n"
            "### Next Steps\n"
            "1. [Clear follow-up question or decision prompt to help the user choose (e.g. asking about timeline, target goal, or risk appetite).]\n"
            "2. [Secondary follow-up question if applicable.]\n\n"
            "STRICT FORMATTING RULES:\n"
            "- DO NOT use any emojis anywhere in your response. Keep the tone strictly professional, clean, and institutional.\n"
            "- Use simple dashes (-) for bullet points and numbers (1., 2.) for ranked lists.\n"
            "- Always use clean line breaks between headers, bullet points, and paragraphs.\n"
            "- Keep points sharp, crisp, and high-signal (avoid repetitive filler).\n"
            "- Scope: Educational and advisory in Indian retail finance (INR). Never guarantee returns or claim to execute trades.\n\n"
            f"SPECIALIST OUTPUTS:\n{json.dumps(state['agent_outputs'], default=str)}\n\n"
            f"MINIMIZED USER CONTEXT:\n{json.dumps(state.get('financial_context', {}), default=str)}\n\n"
            f"SOURCES:\n{source_text}"
        )

        messages = [{"role": "system", "content": system}, *state["history"][-8:], {"role": "user", "content": state["user_message"]}]
        warnings = list(state["warnings"])
        try:
            response = self.llm(messages)
        except Exception as exc:
            warnings.append(f"Chat model unavailable ({type(exc).__name__})")
            response = self._truthful_fallback(state)

        allowed = {item["citation_id"] for item in citations}
        invalid = [citation for citation in CITATION_RE.findall(response) if citation not in allowed]
        for citation in invalid:
            response = response.replace(f"[{citation}]", "[unverified citation removed]")
        if invalid:
            warnings.append("The model emitted an unverified citation; it was removed")
        response, unsupported_numbers = validate_material_numbers(
            response,
            {
                "specialist_outputs": state["agent_outputs"],
                "financial_context": state.get("financial_context", {}),
                "public_sources": citations,
                "user_message": state["user_message"],
            },
        )
        if unsupported_numbers:
            warnings.append("Unsupported material financial figures were removed from the generated response")
        return {"response": response, "warnings": warnings, "completed_nodes": [*state["completed_nodes"], "generate"]}

    @staticmethod
    def _truthful_fallback(state: AgentState) -> str:
        if state["agent_outputs"]:
            summaries = []
            for name, output in state["agent_outputs"].items():
                status = output.get("status", "available")
                details = ChatOrchestrator._specialist_summary(name, output)
                summaries.append(f"**{name.title()} analysis:** status `{status}`. {details}")
            return "The conversational AI service is currently unavailable.\n\n" + "\n".join(summaries)
        return "The conversational AI service is currently unavailable, and no grounded specialist result was requested. Please try again later."

    @staticmethod
    def _specialist_summary(name: str, output: dict) -> str:
        preferred = {
            "portfolio": ("net_worth", "valuation_status", "valuation_coverage"),
            "tax": ("estimated_capital_gains_tax", "status", "rule_version"),
            "cashflow": ("total_income", "total_expenses", "surplus", "transaction_count"),
            "guardian": ("anomaly_count", "sample_count", "model_version"),
        }.get(name, ())
        values = [f"{key.replace('_', ' ')}: {output[key]}" for key in preferred if key in output]
        return "; ".join(values) if values else "No material metric was available."


def run_chat_orchestrator(user_id: str, user_message: str, conversation_id: str, db: Any) -> dict[str, Any]:
    return ChatOrchestrator(db).run(user_id, user_message, conversation_id)
