# Hosted security validation runbook

The committed `security_matrix` results are not a complete security test. Use
this runbook on a **disposable Supabase project** containing synthetic data only.
Never point these procedures at production.

## Environment preparation

1. Create an empty Supabase test project and save its URL and secret/service
   role key in `backend/.env`. Do not commit that file.
2. Apply the new-project migration sequence documented in
   `backend/migrations/SCHEMA_BASELINE.md`, including
   `007_guardian_transaction_time.sql`.
3. Configure a private `quant-secure-ingestion` storage bucket if inbox storage
   is included in the paper's security claims.
4. Use non-production values for `JWT_SECRET_KEY`,
   `CREDENTIAL_ENCRYPTION_KEY`, `INBOX_WEBHOOK_SECRET`, and
   `EXPORT_SIGNING_SECRET`. Leave real broker, email, and customer credentials
   unset.
5. Start the backend in test/development mode, then run the existing destructive
   but self-cleaning smoke test only after checking the target URL:

```powershell
python backend/scripts/smoke_hosted_runtime.py `
  --api-url http://127.0.0.1:8000/api `
  --confirm-hosted-smoke
```

The script creates a uniquely named synthetic user and deletes that exact user
afterward. Its current scope verifies registration, HttpOnly cookie auth,
import preview/commit, user-scoped normalized download, logout, and cleanup.

## Required evidence beyond the smoke test

Record each case in `security_test_matrix_template.csv`. A case is `PASS` only
when the expected behavior is observed through the hosted API or direct
anon/authenticated Supabase client. Source inspection is `INSPECTION_ONLY`, and
an unexecuted case is `NOT_RUN`; neither belongs in a functional pass-rate
denominator.

| Area | Minimum hosted procedure |
| --- | --- |
| RLS | Create two authenticated Supabase users and verify that user B cannot select, update, or delete user A's banking account, transactions, imports, conversations, connector records, or storage objects. Test using user-scoped tokens, not the service-role key. |
| Application authorization | Through the API, attempt user B reads/writes using user A UUIDs for accounts, transactions, imports, chat, connector syncs, dashboard runs, and exports. Expect 404/422 without existence leakage. |
| Cookies and sessions | Verify `HttpOnly`, the intended `SameSite` value, `Secure` under production HTTPS, logout invalidation, expired/tampered JWT rejection, and no token in response bodies beyond the documented login contract. |
| Uploads | Exercise empty, malformed, oversized, duplicate, formula-injection, command-like, wrong-MIME, and cross-user import/download cases. Confirm ignored columns and failure messages do not expose another user's data. |
| Storage and signed downloads | Verify the bucket is private, object keys are user-scoped, signatures expire, modified/expired tokens fail, and another user cannot download by guessing a key or export ID. |
| Connector payloads | Use the sandbox/mock transport with hostile instruction strings, malformed numbers, duplicate item IDs, authorization expiry, retry, preview-before-commit, idempotent commit, and revocation. Confirm credentials/tokens never appear in API responses or logs. |
| Prompt injection | Submit hostile imported text, retrieved-document text, and connector fields. Verify they remain data, do not alter routing/tool authority, and cause review/blocking where the policy requires it. |
| Cleanup | Verify every synthetic user and cascaded record is removed. Retain only the redacted result matrix, environment versions, migration commit, and non-sensitive logs. |

## Reporting

Report counts as `functional_pass / functional_executed`, followed separately
by failures, inspection-only checks, and not-run checks. Include the tested Git
commit, migration list, Supabase/Postgres versions, API deployment mode, UTC
timestamps, and sanitized evidence. Describe this as representative control
validation, not a penetration test or proof of complete security.
