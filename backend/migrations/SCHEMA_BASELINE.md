# Canonical schema baseline

The runtime architecture uses the synchronous Supabase Python client through user-scoped repositories. SQL migrations in this directory are authoritative; `models/models.py` is not a runtime schema source.

Canonical primary keys:

| Entity | Table | Primary key |
|---|---|---|
| User | `users` | `user_id` |
| Bank account | `banking_accounts` | `account_id` |
| Equity holding | `equity_holdings` | `equity_holding_id` |
| Mutual fund holding | `mutual_fund_holdings` | `mf_holding_id` |
| ETF holding | `etf_holdings` | `etf_holding_id` |
| Crypto holding | `crypto_holdings` | `crypto_holding_id` |
| Bank transaction | `bank_transactions` | `bank_tx_id` |
| Goal | `goals` | `goal_id` |
| Conversation | `chat_conversations` | `conversation_id` |
| Message | `chat_messages` | `message_id` |
| Dashboard run | `dashboard_runs` | `run_id` |
| Broker connection | `connector_accounts` | `connector_account_id` |
| Notification | `notifications` | `notification_id` |
| Guardian event | `guardian_events` | `guardian_event_id` |
| Risk assessment | `risk_assessments` | `risk_assessment_id` |
| Historical market price | `market_price_history` | `price_history_id` |

The service-role key is backend-only. Every application query still filters by `user_id`; service-role bypass is not treated as authorization. Tables have RLS enabled defensively, with no public policies in these migrations.

There are two mutually exclusive migration paths:

- A new/empty project applies `001_canonical_core.sql`, then `002_recovery_services.sql`, `004_service_role_grants.sql`, `005_future_scope.sql`, and finally `006_portfolio_analytics.sql`.
- The existing hosted legacy project applies `003_hosted_legacy_compatibility.sql` after a backup and staging rehearsal, followed by `004_service_role_grants.sql`, `005_future_scope.sql`, and `006_portfolio_analytics.sql`. Projects that applied an earlier copy of 003 still apply the privilege-only 004 follow-up.

The hosted compatibility migration was generated from a read-only PostgREST schema inventory. It preserves legacy columns and data, adds canonical columns alongside them, and deliberately leaves `document_embeddings` and `match_documents` untouched. Personal financial rows are not embedded by the runtime; Qdrant is the active RAG store for curated public knowledge.

Never apply both paths to the same populated project without a fresh schema comparison.
