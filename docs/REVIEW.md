# Code Review Checklist (2026-07-19)

Findings from a full backend + frontend audit. Track fixes here; feature ideas that were already tracked in [TASKS.md](TASKS.md) stay there.

## 🟡 Half-implemented features

- [x] `transactions_updated` always 0 — plumbed through models/DB/UI, never incremented (`sync_service.py:63,232`). Fixed: `TransactionRepository.persist` now compares incoming rows against stored ones and returns `(new_transactions, updated_count)` — unchanged rows are skipped entirely (no more pointless rewrites every sync), changed rows (e.g. pending→booked) count as updated and flow into the sync result (`test_transaction_repository.py`).
- [ ] `POST /notifications/test` ignores the user's message, sends a canned expiry notification (`notification_service.py:181-209`); Discord/Telegram test buttons give zero UI feedback (`DiscordConfigDrawer.tsx:71-77`, `TelegramConfigDrawer.tsx:73-78`).
- [ ] Settings can't be cleared: empty notification filter lists skipped on save (`routes/notifications.py:82-91`); S3 config can't be removed via API (`routes/backup.py:80-95`).
- [x] `maximum_consent_validity` plumbed but never passed — consents hardcoded to 90 days (`enablebanking_service.py:80`, `routes/banks.py:55-60`). Fixed: `POST /banks/connect` looks up the ASPSP via the (cached) `get_aspsps` call and forwards its `maximum_consent_validity` to `start_auth`, so consents are requested for the longest validity the bank supports; the 90-day default remains only for banks that don't report one.
- [x] Deep-link search params (`accountId`/`startDate`/`endDate`) declared but never read (`routes/index.tsx:6-10`). Fixed (removed): nothing in the app wrote these params either, so the dead `validateSearch` declaration was deleted. Real URL-driven filters on the transactions page stay a candidate feature.
- [ ] Backup restore exists in API but has no UI.
- [ ] `GET /auth/status` always returns `auth_enabled: true`; frontend caller is dead (`routes/auth.py:46-49`, `api.ts:487`).
- [x] `[database] sqlite` config section is a no-op (`utils/config.py:200`); remove from config + example. Fixed: `DatabaseConfig`, the `database_config` property, and the `[database]` sections in `config.example.toml`/README are gone. Legacy configs that still contain `[database]` load fine (Pydantic ignores unknown sections — covered by a test).
- [ ] `generate_sample_db --force` doesn't overwrite (old rows persist); printed instructions use invalid `leggen server --database X` ordering (`generate_sample_db.py:662-679`).

## 🎨 Consistency

- [ ] CLI: exit non-zero on failure everywhere (currently `return` after catch → exit 0); `bank/delete.py` missing health check and error handling; unify stderr `error()` vs stdout `click.echo`.
- [ ] API error conventions: stop embedding `str(e)` in 500 bodies (path/SQL leakage — categories routes already sanitize, copy that); `POST /sync` should return 409 not 500 for "already running"; unify `limit`/`offset` vs `page`/`per_page`.
- [ ] `NotificationService.active` is the real on/off signal; `Settings.tsx:305-320` derives status from `enabled && configured` — "Needs Configuration" state unreachable.
- [ ] Naming drift (larger effort, needs migration): `institution_id` stores ASPSP name, `balances.bank`, camelCase `transactions` columns vs snake_case elsewhere, `internalTransactionId` holding `entry_reference`.
- [ ] Balances table: add `UNIQUE(account_id, type, timestamp)` or skip-if-unchanged dedup — currently unbounded append growth; the `IntegrityError` handler at `balance_repository.py:67` is dead code.
- [ ] Pending→booked reconciliation: pending rows keyed by `entry_reference` are never removed when the booked version arrives (`data_processors.py:477-481`).

## 🔧 CI / tooling

- [ ] Add `ruff check` + `mypy` to CI (currently pytest only, `.github/workflows/ci.yml`).
- [ ] Gate `release.yml` on tests (currently any tag ships to PyPI/Docker).
- [ ] Add tests for the riskiest untested code: `migration_repository.py` (840 lines, zero coverage), `data_processors.py`, `enablebanking_service.py`, repositories, CLI commands (the `cli` marker exists, unused — would have caught the bank-group break).
- [ ] Add a frontend test runner (vitest) — currently zero frontend tests.
- [ ] Backend Dockerfile: non-root `USER`; drop the redundant dev-group `uv sync` layer.
- [ ] Fix `.dockerignore` entry `docker-compose.dev.yml` → `compose.dev.yml`.
- [ ] Docs: add S3 backup to README features; fix frontend/README "Node 18+" (Vite 7 needs 20.19+); fix `frontend/package.json` version `0.0.0`.

## ✨ New feature ideas (not yet in TASKS.md)

- [ ] Net-worth / balance-over-time dashboard on the overview page — `/balances/history` and per-sync snapshots already exist.
- [ ] Data-driven bank names/logos in analytics — accounts table stores `logo`; kills the hard-coded 3-bank map (`TransactionDistribution.tsx:41`).
- [ ] Pending-transaction filter/visual distinction — `transactionStatus` is stored and counted but not surfaced.
- [ ] Per-currency stats grouping (prerequisite for meaningful totals with multi-currency accounts).
- [ ] Notification history table — persists sent notifications, gives `/notifications` a purpose (overlaps TASKS.md "Stale route" item).

Already tracked in [TASKS.md](TASKS.md): budgets, recurring detection, rules, CSV export, onboarding, transaction detail view, keyboard nav, multi-select, migrations framework, error consistency, notes/attachments.

## 🗣️ To be discussed later

- [ ] Account deletion is really an "archive" feature — decide the semantics and make code/UX coherent. Accounts are keyed by IBAN on purpose (stable identity across sessions, `sync_service.py:135`), so a "deleted" account under an active bank connection comes back on the next sync — that's intended. What's incoherent today: sync overwrites the `DELETED` status back to `READY` (`sync_service.py:141`), losing the archive flag; `delete_data=true` purges history that sync then partially re-imports (last 30 days), leaving a permanent hole; the "skip deleted accounts" block (`sync_service.py:103-109`) compares IBANs to session UIDs and is dead code; and there's no unarchive action or archived-accounts filter (`GET /accounts` returns them by default, `account_repository.py:93`). Proposed shape: rename to Archive in UI/API, sync preserves the archived status, drop `delete_data` and the dead exclusion block, hide archived accounts from default views with a toggle, add unarchive. Open question: should archived accounts keep syncing in the background (recommended) or be skipped?
