# Future-scope operations

## Database

Apply `migrations/005_future_scope.sql` after migrations 001–004. It creates broker, notification, job, ingestion, Guardian, personalization, export and analytics records plus the private `quant-secure-ingestion` Storage bucket.

Apply `migrations/006_portfolio_analytics.sql` after 005. It adds only the user-scoped historical market-price table used for measured beta and Markowitz research allocations. The table has RLS enabled and receives only a table-specific backend service-role grant.

Set a strong independent `CREDENTIAL_ENCRYPTION_KEY` before connecting any provider. Changing it without a key-rotation procedure makes existing encrypted credentials and files unreadable.

## Worker

Run the worker separately from FastAPI:

```powershell
cd backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m scripts.run_worker
```

The worker claims due schedules through `claim_due_job_schedules`, records idempotent `job_runs`, and handles price refresh and Guardian events. API requests only enqueue work.

## Upstox

Configure `UPSTOX_CLIENT_ID`, `UPSTOX_CLIENT_SECRET` and the exact registered `UPSTOX_REDIRECT_URI`. Interactive OAuth is read-only in QUANT. Standard access tokens may require reauthorization; QUANT never fabricates a refresh-token lifecycle.

Long-lived Upstox analytics tokens are not accepted through the current UI. Official documentation says account/portfolio access with these tokens requires requests from the configured static IP: https://upstox.com/developer/api-documentation/analytics-token/

## Forwarding inbox

Configure `INBOX_WEBHOOK_SECRET` and route the provider's attachment webhook to `POST /api/ingestion-inbox/receive/{address_token}`. The webhook must send `X-QUANT-Inbox-Secret`, `external_message_id`, `sender` and one attachment.

The built-in scanner rejects executable signatures, EICAR, encrypted/unsafe spreadsheet archives, invalid PDFs and unsupported formats. A production mail ingress should additionally run an independently managed malware scanner before calling QUANT.

## Notifications

The browser uses authenticated SSE at `/api/notifications/stream`. Email deliveries remain pending until an approved transactional-email adapter is configured; outbound payload construction always applies financial-secret redaction.

## Exports

Dashboard exports use five-minute user-bound signed download tokens. They contain the selected period, generation/data-as-of times, valuation coverage and sources. Export responses are `no-store`.
