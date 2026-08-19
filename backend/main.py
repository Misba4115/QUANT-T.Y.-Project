"""QUANT FastAPI application entry point."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.capabilities import build_capability_registry, legacy_readiness_status
from core.config import get_settings
from core.request_context import RequestIdMiddleware, install_error_handlers
from db.supabase_client import get_supabase_client
from routers import analytics, auth, banking, capabilities, chat, connectors, dashboard, goals, guardian_stream, holdings, imports, ingestion_inbox, insights, jobs, market_data, notifications, personalization, rag, transactions, user

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title=settings.app_name,
    description="Multi-agent financial intelligence for Indian retail investors",
    version="1.1.0",
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


install_error_handlers(app)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(banking.router, prefix="/api/banking-accounts", tags=["Banking"])
app.include_router(holdings.router, prefix="/api/holdings", tags=["Holdings"])
app.include_router(imports.router, prefix="/api/imports", tags=["Imports"])
app.include_router(market_data.router, prefix="/api/market-data", tags=["Market Data"])
app.include_router(rag.router, prefix="/api/rag", tags=["RAG"])
app.include_router(connectors.router, prefix="/api/connectors", tags=["Connectors"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(ingestion_inbox.router, prefix="/api/ingestion-inbox", tags=["Ingestion Inbox"])
app.include_router(guardian_stream.router, prefix="/api/guardian", tags=["Guardian"])
app.include_router(personalization.router, prefix="/api/personalization", tags=["Personalization"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(goals.router, prefix="/api/goals", tags=["Goals"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(insights.router, prefix="/api/insights", tags=["Insights"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(capabilities.router, prefix="/api/capabilities", tags=["Capabilities"])
app.include_router(insights.router, prefix="/api/insights", tags=["Insights"])
app.include_router(user.router, prefix="/api", tags=["User"])


@app.get("/", tags=["Health"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "quant-api",
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/readiness", tags=["Health"])
def readiness() -> dict:
    registry = build_capability_registry(settings)
    dependency_names = [
        "database", "llm", "qdrant", "market_data", "worker", "smtp", "upstox",
        "ingestion_inbox", "parsers", "insights", "grounding_checker", "consensus_arbiter",
        "outcome_evaluator",
    ]
    dependencies = {}
    for name in dependency_names:
        capability = registry.capabilities[name]
        dependencies[name] = {
            **capability.model_dump(mode="json"),
            "capability_status": capability.status,
            "status": legacy_readiness_status(capability.status),
        }
    # Compatibility alias retained until clients move from statement_inbox.
    dependencies["statement_inbox"] = {**dependencies["ingestion_inbox"]}

    if settings.database_configured:
        try:
            database = get_supabase_client()
            database.table("users").select("user_id").limit(1).execute()
            database.table("import_batches").select("import_batch_id").limit(1).execute()
            database.table("connector_accounts").select("connector_account_id").limit(1).execute()
            database.table("notifications").select("notification_id").limit(1).execute()
            database.table("job_schedules").select("job_schedule_id").limit(1).execute()
            dependencies["database"]["capability_status"] = "available"
            dependencies["database"]["status"] = "ready"
            dependencies["database"]["reason_code"] = "live_probe_passed"
            dependencies["database"]["freshness"] = "fresh"
            dependencies["database"]["data_as_of"] = datetime.now(timezone.utc).isoformat()
        except Exception:
            dependencies["database"]["capability_status"] = "failed"
            dependencies["database"]["status"] = "error"
            dependencies["database"]["reason_code"] = "live_probe_failed"
            dependencies["database"]["retryable"] = True
            dependencies["database"]["detail"] = "Configured but unreachable or required migrations are missing"

    if settings.qdrant_url:
        from services.qdrant_rag_service import probe_public_knowledge

        qdrant = probe_public_knowledge()
        dependencies["qdrant"].update(qdrant)
        dependencies["qdrant"]["capability_status"] = qdrant["status"]
        dependencies["qdrant"]["status"] = legacy_readiness_status(qdrant["status"])

    required_ready = dependencies["database"]["status"] == "ready"
    return {
        "status": "ready" if required_ready else "degraded",
        "required_ready": required_ready,
        "contract_version": registry.contract_version,
        "status_vocabulary": registry.status_vocabulary,
        "dependencies": dependencies,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
