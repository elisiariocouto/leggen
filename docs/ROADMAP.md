# Roadmap

> Line references drift as the code moves. Verify them before starting an item —
> and re-check the claim itself, since a refactor may already have fixed it.

## 🎨 Consistency & code quality

- [ ] `decode_access_token` (`utils/auth.py:37-43`) catches expired and malformed tokens in one `except` and returns `None` for both, so the API can't tell the frontend to refresh rather than force a re-login.
- [ ] The `active` field on the notification status model (`api/models/notifications.py:38`) is the real on/off signal, but `Settings.tsx:342-354` derives status from `enabled && configured` — the "Needs Configuration" state is unreachable.
- [ ] Notification error semantics (do these together, they're one pass): `send_test_notification` (`services/notification_service.py:40-56`) returns a bare `False` for both "service not enabled" and "the provider call raised", so `POST /notifications/test` answers a misconfiguration and a network failure with an identical 400 — needs domain errors (`NOTIFICATION_NOT_ENABLED`, plus a 502 for upstream send failures) and a frontend that keys off `code`; `DELETE /notifications/settings/{service}` (`api/routes/notifications.py:163-169`) still hand-validates the service name and returns 400, now inconsistent with the `Literal` 422 on the test endpoint.
- [ ] `escape_markdown` (`notifications/telegram.py:6`) never escapes backslash, and backslash must be escaped first — text containing one produces an invalid MarkdownV2 sequence and an opaque Telegram 400. Currently unreachable (only bank names and error strings flow through) but a trap for any future path that sends user-supplied text.
- [ ] `mock_config` (`tests/conftest.py:110`) assigns to the process-global `config` singleton at `conftest.py:136-137` and never restores it, so config a test sets leaks into every later test in the session. `reset_config_singleton()` (`conftest.py:160`) already does the cleanup — the fixture just needs to call it after the `yield`. Note the `patch("leggen.utils.config.config", ...)` in existing tests is a no-op: modules bound `config` at import time, and the tests only pass because `Config.__new__` (`utils/config.py:20-23`) returns the same singleton the fixture mutates.

## 🔧 Testing & CI

- [ ] Raise coverage on the least-tested modules. Overall is 73%; the weak spots are `sync_repository.py` (20%), `category_repository.py` (29%), `account_repository.py` (44%), `data_processors.py` (48%) and `enablebanking_service.py` (57%). Measure with `uv run --with pytest-cov pytest --cov=leggen --cov-report=term-missing` before picking targets. Already well covered: the migration runner (100%), `db.py` (100%), `session_repository.py` (98%), `transaction_repository.py` (84%), and CLI commands (`tests/unit/test_cli_commands.py`, `cli` marker).

## 🖥️ Features — UI/UX

- [ ] Surface pending transactions in the transactions table and filters. `transaction_status` is stored and typed (`frontend/src/types/api.gen.ts:1625`) and already rendered as a `<StatusBadge>` in `TransactionDetail.tsx:198`, but the table shows no visual distinction and there is no filter for it.

---

## 🗣️ To be discussed later

- [ ] Account deletion is really an "archive" feature — decide the semantics and make code/UX coherent. Accounts are keyed by IBAN on purpose (stable identity across sessions), so a "deleted" account under an active bank connection comes back on the next sync — that's intended. Sync now genuinely skips DELETED accounts (`sync_service.py:130-136` subtracts them by ID), but `sync_service.py:195` still hardcodes `"status": "READY"` when persisting synced accounts; `delete_data=true` purges history that sync then partially re-imports (last 30 days), leaving a permanent hole; and there's no unarchive action or archived-accounts filter (`GET /accounts` returns them by default — `get_accounts(include_deleted=True)`, `account_repository.py:60-63`). Proposed shape: rename to Archive in UI/API, sync preserves the archived status, drop `delete_data`, hide archived accounts from default views with a toggle, add unarchive. Open question: should archived accounts keep syncing in the background (recommended) or be skipped?
- [ ] Balances table: add `UNIQUE(account_id, type, timestamp)` or skip-if-unchanged dedup — currently unbounded append growth. No unique constraint exists on the table (`repositories/migrations/_steps.py:110`), so the `IntegrityError` handler in `balance_repository.py:33-34` is dead code.
- [ ] Pending→booked reconciliation: pending rows keyed by the `entry_reference` fallback (`data_processors.py:636-647`) are never removed when the booked version arrives — `persist` is `INSERT OR REPLACE` on `(accountId, transactionId)`, so the booked row gets a different key and the pending row lingers.
- [ ] Recurring transaction detection - Automatically detect subscriptions and recurring payments (Netflix, rent, salary) by analyzing patterns. Show them in a dedicated view with expected upcoming charges.
- [ ] Spending rules/automation - Auto-categorize transactions based on user-defined rules (e.g., "if description contains 'LIDL' → Groceries"). Currently only keyword learning exists, but explicit rules would give users more control.
- [ ] Empty states & onboarding - When a user first opens the app with no bank connections, there's no guided onboarding flow. A first-run wizard or prominent call-to-action on the dashboard would help.
- [ ] Keyboard navigation - No keyboard shortcuts for common actions (j/k to move between transactions, c to categorize, / to search). Power users managing hundreds of transactions would benefit greatly.
- [ ] Multi-select transactions - Currently bulk operations only work by description match. Being able to select multiple transactions with checkboxes and then bulk-categorize, export, or tag them would be more flexible.
- [ ] Net-worth / balance-over-time dashboard on the overview page — `/balances/history` and per-sync snapshots already exist.
- [ ] Per-currency stats grouping (prerequisite for meaningful totals with multi-currency accounts).
- [ ] Notification history - Persist sent notifications (Discord/Telegram) with their content and delivery status, and show a history/inbox view. Today only expiry notifications are persisted (`session_repository.py:29`); the old stale `/notifications` route has since been removed, so this would be a brand-new page.
