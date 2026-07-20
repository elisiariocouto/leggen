# Roadmap

## 🐛 Bugs & half-implemented features

- [ ] `POST /notifications/test` ignores the user's message — `_send_discord_test`/`_send_telegram_test` build a hardcoded expiry payload and call `send_expire_notification`; the `message` field is only logged (`notification_service.py:189-210`). (The frontend half is done: both drawers now show sonner toasts on success/failure.)
- [ ] Settings can't be cleared: empty notification filter lists are skipped on save — truthiness checks on the filter lists and on `filters_config` (`routes/notifications.py:100-108`); S3 backup config has no DELETE endpoint and PUT only acts `if settings.s3:` (`routes/backup.py` — copy the notifications DELETE at `routes/notifications.py:185`).
- [ ] Backup restore exists in the API (`routes/backup.py:227-243`) and the API client (`api.ts:386`), but the only wired UI action is "Backup Now" (`Settings.tsx:141,535`) — no restore UI.
- [ ] `generate_sample_db --force` doesn't truly overwrite: `INSERT OR REPLACE` for accounts/transactions but plain `INSERT` for balances, and tables are never dropped — old rows persist (`generate_sample_db.py:333,355,380`); printed instructions still use invalid ordering `leggen server --database X` (`generate_sample_db.py:549`) — `--database` is a global option and must precede the subcommand.

## 🎨 Consistency & code quality

- [ ] CLI: exit non-zero on failure everywhere — `sync.py:58-59` and `status.py:24` catch and `return` → exit 0; `bank/delete.py` has no health check and no error handling (`delete.py:26`), unlike its siblings; unify stderr `error()` vs stdout `click.echo`.
- [ ] API error consistency - Some endpoints catch generic Exception, and error response formats vary. A unified error response schema would improve the frontend's ability to show meaningful error messages. (500 bodies are already sanitized to static messages; what's missing is the unified schema.)
- [ ] `NotificationService.active` is the real on/off signal; `Settings.tsx:323-327` derives status from `enabled && configured` — "Needs Configuration" state unreachable.
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
