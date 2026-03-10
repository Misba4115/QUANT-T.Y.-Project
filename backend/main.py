"""
QUANT — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, banking, holdings, transactions, goals, dashboard, chat

app = FastAPI(
    title="QUANT API",
    description="Multi-Agent AI Financial Advisor for Indian Retail Investors",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:5173",  # Vite/React dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,         prefix="/auth",             tags=["Auth"])
app.include_router(banking.router,      prefix="/banking-accounts", tags=["Banking"])
app.include_router(holdings.router,     prefix="/holdings",         tags=["Holdings"])
app.include_router(transactions.router, prefix="/transactions",     tags=["Transactions"])
app.include_router(goals.router,        prefix="/goals",            tags=["Goals"])
app.include_router(dashboard.router,    prefix="/dashboard",        tags=["Dashboard"])
app.include_router(chat.router,         prefix="/chat",             tags=["Chat"])


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "QUANT API is running"}
