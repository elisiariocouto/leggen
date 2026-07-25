# Roadmap

## 🐛 Bugs & half-implemented features

- [x] `POST /notifications/test` sent a hardcoded expiry payload and only logged the request's `message`. A user-composed test message isn't a useful feature, so the `message` field was removed from the request model, the service, and both config drawers instead of being wired through; the endpoint now sends a fixed payload that identifies itself as a test rather than impersonating an account-expiry notice. `service` is a `Literal`, so an unknown service is a 422 through the error envelope instead of a generic 400, and the endpoint has tests for the first time.
- [x] Settings can now be cleared. `PUT /notifications/settings` dropped empty filter lists behind truthiness checks and then skipped the write entirely, so removing the last filter reported success and changed nothing; empty lists are honoured and the section is always written. Making empty payloads meaningful exposed that `update_section` replaces a section wholesale, so the handler now merges against what is stored and reads `model_fields_set`: an omitted field is left alone, an explicit null removes a service, an empty list clears a filter list. `DELETE /backup/settings` and `DELETE /notifications/settings/filters` remove a section outright — the latter declared ahead of `/{service}`, which would otherwise match `filters` and reject it — and a `PUT /backup/settings` carrying no `s3` config is a 400 pointing at the DELETE instead of a 200 that did nothing. The S3 drawer gained a Remove configuration action behind a confirmation dialog, so the stored credentials can be deleted rather than only disabled.
- [ ] Cleared sections are written as empty tables (`[filters]` with two empty lists, a bare `[backup]`) rather than removed from `config.toml`. Services treat empty and absent identically, so this is cosmetic; removing them needs a `delete_section` on the config singleton, since `update_section` only replaces (`utils/config.py:103`).
- [ ] The notification services and filters have DELETE endpoints, but `PUT /notifications/settings` can also remove a service by sending an explicit null — two ways to do one thing, and the frontend uses neither for filters (it clears by sending empty lists).
- [ ] Backup restore exists in the API (`routes/backup.py:227-243`) and the API client (`api.ts:386`), but the only wired UI action is "Backup Now" (`Settings.tsx:141,535`) — no restore UI.
- [ ] `generate_sample_db --force` doesn't truly overwrite: `INSERT OR REPLACE` for accounts/transactions but plain `INSERT` for balances, and tables are never dropped — old rows persist (`generate_sample_db.py:333,355,380`); printed instructions still use invalid ordering `leggen server --database X` (`generate_sample_db.py:549`) — `--database` is a global option and must precede the subcommand.

## 🎨 Consistency & code quality

- [ ] CLI: exit non-zero on failure everywhere — `sync.py:58-59` and `status.py:24` catch and `return` → exit 0; `bank/delete.py` has no health check and no error handling (`delete.py:26`), unlike its siblings; unify stderr `error()` vs stdout `click.echo`.
- [x] API error consistency - Every error response now carries the same envelope (`ErrorResponse` in `api/models/common.py`): a string `detail`, a machine-readable `code`, the `status`, and field-level `errors` on 422. Exception handlers in `api/errors.py` shape all of them, including the cases routes never saw — unhandled exceptions (previously a plain-text 500) and unknown routes. Domain errors live in `leggen/errors.py`. The frontend's `getApiError` parses the envelope; `getApiErrorMessage` keeps its signature, so its 24 call sites were untouched. Validation errors no longer echo the submitted value, which leaked secrets rejected by validation.
- [ ] `DELETE /categories/{id}` returns 400 for "not found or is a default category" (`routes/categories.py:112`), conflating two cases and disagreeing with the 404s elsewhere. Splitting them into 404 vs 409/403 is a behaviour change — `test_api_categories.py:191` asserts the 400.
- [ ] `decode_access_token` returns None for both expired and malformed tokens (`utils/auth.py:38-44`), so the API can't tell the frontend to refresh rather than force a re-login.
- [ ] Per-form 422 field errors: the envelope carries them and `getApiFieldErrors` exposes them, but no form maps them back to inputs — that needs a field-path-to-input registry per drawer.
- [ ] `NotificationService.active` is the real on/off signal; `Settings.tsx:323-327` derives status from `enabled && configured` — "Needs Configuration" state unreachable.
- [ ] Notification error semantics (do these together, they're one pass): `send_test_notification` returns a bare `False` for both "service not enabled" and "the provider call raised", so `POST /notifications/test` answers a misconfiguration and a network failure with an identical 400 — needs domain errors (`NOTIFICATION_NOT_ENABLED`, plus a 502 for upstream send failures) and a frontend that keys off `code`; `DELETE /notifications/settings/{service}` still hand-validates the service name and returns 400, now inconsistent with the `Literal` 422 on the test endpoint.
- [ ] `escape_markdown` (`notifications/telegram.py:6`) never escapes backslash, and backslash must be escaped first — text containing one produces an invalid MarkdownV2 sequence and an opaque Telegram 400. Currently unreachable (only bank names and error strings flow through) but a trap for any future path that sends user-supplied text.
- [ ] `mock_config` (`tests/conftest.py:136`) assigns to the process-global `config` singleton's `_config` without restoring it, so config a test sets leaks into every later test in the session. Note the `patch("leggen.utils.config.config", ...)` in existing tests is a no-op — modules bound `config` at import time, and the tests only pass because `Config.__new__` returns the same singleton the fixture mutates.
- [ ] Naming drift (larger effort, needs migration): `institution_id` stores ASPSP name, `balances.bank`, camelCase `transactions` columns vs snake_case elsewhere, `internalTransactionId` holding `entry_reference`.
- [ ] Balances table: add `UNIQUE(account_id, type, timestamp)` or skip-if-unchanged dedup — currently unbounded append growth; no unique constraint exists, so the `IntegrityError` handler in `balance_repository.py:54-68` is dead code.
- [ ] Pending→booked reconciliation: pending rows keyed by `entry_reference` fallback (`data_processors.py:519-526`) are never removed when the booked version arrives — `persist` is `INSERT OR REPLACE` on `(accountId, transactionId)`, so the booked row gets a different key and the pending row lingers.

## 🔧 Testing & CI

- [ ] Add tests for the riskiest untested code: `migration_repository.py` (zero coverage), `data_processors.py` (only indirectly patched), `enablebanking_service.py` (only mocked in API tests), repositories other than transactions. CLI commands now have basic coverage (`tests/unit/test_cli_commands.py`, `cli` marker).
- [ ] Add a frontend test runner (vitest) — currently zero frontend tests, no `test` script.
- [ ] Backend Dockerfile: non-root `USER` — deliberately deferred: compose deployments bind-mount `./data:/root/.config/leggen`, so going non-root breaks existing volume paths/ownership; needs a coordinated path change (e.g. `LEGGEN_CONFIG_DIR=/data`).

## 💰 Features — Financial

- [ ] Budget tracking - Define monthly/weekly budgets per category, with progress bars and alerts when nearing limits. This is arguably the #1 missing feature for a personal finance tool.
- [ ] Recurring transaction detection - Automatically detect subscriptions and recurring payments (Netflix, rent, salary) by analyzing patterns. Show them in a dedicated view with expected upcoming charges.
- [ ] Spending rules/automation - Auto-categorize transactions based on user-defined rules (e.g., "if description contains 'LIDL' → Groceries"). Currently only keyword learning exists, but explicit rules would give users more control.
- [ ] CSV/data export - No export functionality exists. Users should be able to export transactions as CSV/OFX for tax purposes or migration.

## 🖥️ Features — UI/UX

- [ ] Empty states & onboarding - When a user first opens the app with no bank connections, there's no guided onboarding flow. A first-run wizard or prominent call-to-action on the dashboard would help.
- [x] Transaction detail view - Clicking a transaction opens a formatted detail panel (`TransactionDetail.tsx`, Sheet on desktop / Drawer on mobile) with counterparty, status, dates, references, inline categorization and collapsible raw JSON. Category history was skipped — the backend only stores the current category (no audit trail).
- [ ] Keyboard navigation - No keyboard shortcuts for common actions (j/k to move between transactions, c to categorize, / to search). Power users managing hundreds of transactions would benefit greatly.
- [ ] Multi-select transactions - Currently bulk operations only work by description match. Being able to select multiple transactions with checkboxes and then bulk-categorize, export, or tag them would be more flexible.
- [ ] Pending-transaction filter/visual distinction — `transaction_status` is stored and typed (`types/api.ts:112`) but never surfaced in the transactions table or filters.
- [ ] Net-worth / balance-over-time dashboard on the overview page — `/balances/history` and per-sync snapshots already exist.
- [ ] Per-currency stats grouping (prerequisite for meaningful totals with multi-currency accounts).

## ⚙️ Features — Technical

- [ ] Database migrations system - The codebase has ad-hoc migration functions scattered in the migration repository. A proper migration framework (like Alembic or even a simple versioned migration system) would prevent schema drift issues.
- [ ] Notification history - Persist sent notifications (Discord/Telegram) with their content and delivery status, and show a history/inbox view. Today only expiry notifications are persisted (`session_repository.py:29`); the old stale `/notifications` route has since been removed, so this would be a brand-new page.

## ✨ Nice-to-haves

- [ ] Transaction notes/attachments - Let users add personal notes or attach receipt photos to transactions.

## 🗣️ To be discussed later

- [ ] Account deletion is really an "archive" feature — decide the semantics and make code/UX coherent. Accounts are keyed by IBAN on purpose (stable identity across sessions, `sync_service.py:135`), so a "deleted" account under an active bank connection comes back on the next sync — that's intended. Sync now genuinely skips DELETED accounts (`sync_service.py:125-131` subtracts them by ID), but `sync_service.py:190` still hardcodes `"status": "READY"` when persisting synced accounts; `delete_data=true` purges history that sync then partially re-imports (last 30 days), leaving a permanent hole; and there's no unarchive action or archived-accounts filter (`GET /accounts` returns them by default, `account_repository.py:93`). Proposed shape: rename to Archive in UI/API, sync preserves the archived status, drop `delete_data`, hide archived accounts from default views with a toggle, add unarchive. Open question: should archived accounts keep syncing in the background (recommended) or be skipped?
