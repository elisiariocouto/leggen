# Code Review Checklist (2026-07-19)

Findings from a full backend + frontend audit. Track fixes here; feature ideas that were already tracked in [TASKS.md](TASKS.md) stay there.

## 🔴 Critical — data loss / broken features

- [x] Masked-secret round-trip destroys credentials: `PUT /notifications/settings` persists `"***"` verbatim (`leggen/api/routes/notifications.py:60-99`); frontend pre-fills masked values and sends them back (`NotificationFiltersDrawer.tsx:50-54`, `DiscordConfigDrawer.tsx:41-45`, `TelegramConfigDrawer.tsx:40-44`). Fixed: `resolve_secret` in `leggen/utils/masking.py` treats an echoed `"***"` as "keep the stored value" on PUT (400 when nothing is stored).
- [x] S3 settings can't be edited without re-typing both credentials — masked `"***"` creds fail the connection-test gate (`S3BackupConfigDrawer.tsx:46-49`, `leggen/api/routes/backup.py:71`). Fixed: masked creds resolve to stored values before the connection test on `PUT /backup/settings` and `POST /backup/test`.
- [x] Composite-key migration silently deletes transactions whose raw JSON lacks camelCase `transactionId` (EnableBanking uses snake_case `transaction_id`) (`migration_repository.py:345-375`). Fixed: key probe now uses the same fallback chain as the sync path (`transaction_id` → `transactionId` → `entry_reference` → `internalTransactionId`), the migration aborts before dropping anything if any row has no derivable ID, and it logs migrated vs. source counts. Low impact in practice — only legacy single-PK databases run this path.
- [x] Two `SyncService` instances defeat the "already running" guard → concurrent syncs, duplicate rows, `database is locked` (`background/scheduler.py:13`, `api/routes/sync.py:17`). Fixed: the guard is now a class-level `asyncio.Lock` (with class-level `_sync_status`) shared by all instances, and the sync route reuses `scheduler.sync_service` instead of constructing a duplicate.
- [x] SQLite connections opened without `PRAGMA foreign_keys=ON`, WAL mode, or tuned `busy_timeout` (`repositories/db.py:12`) — `ON DELETE CASCADE` never fires; deleting a category orphans `transaction_categories`/`category_keywords` rows. Fixed: all connections now go through `create_connection()` in `repositories/db.py` (foreign_keys ON, WAL, 10s busy_timeout) — including the 16 raw `sqlite3.connect` call sites in `migration_repository.py`, `data_processors.py`, and `generate_sample_db.py`; a cleanup migration removes rows already orphaned by pre-enforcement deletes.
- [x] `leggen bank add`/`delete` unreachable — `commands/bank/` lost its `__init__.py` (commit `de3da84`); `leggen bank` crashes with `AttributeError` (`leggen/main.py:54-76`). Fixed: restored `commands/bank/__init__.py` with the `BankGroup` discovery group, switched `add`/`delete` to plain `@click.command()`, made `get_command` return `None` instead of raising on missing attributes, and added CLI discovery tests (`tests/unit/test_cli_commands.py`).
- [ ] `leggen --help` crashes with `FileNotFoundError` when config is missing, and silently creates a DB — route modules instantiate `NotificationService()`/`SyncService()` at import time (`routes/notifications.py:17`, `routes/sync.py:17`, `sync_service.py:35`).
- [ ] `generate_auth_config` requires an already-valid config (group-level eager validation, `main.py:79-91`) — chicken-and-egg; same for `generate_sample_db`.
- [ ] Frontend treats success as failure: "Backup Now" checks `response.success` but backend returns `{completed: true}` (`Settings.tsx:126-131`, `backup.py:196`); S3 test checks `success` vs `{connected: true}` (`S3BackupConfigDrawer.tsx:77-84`, `backup.py:228`).
- [ ] Disabled state can never be saved: Save button `disabled` includes `!config.enabled` in all three config drawers (`DiscordConfigDrawer.tsx:164`, `TelegramConfigDrawer.tsx:186`, `S3BackupConfigDrawer.tsx:237`).

## 🟠 High — bugs users will hit

- [ ] `date_to` excludes the end date: `transactionDate` stored as `"YYYY-MM-DD HH:MM:SS"` compared lexically against `"YYYY-MM-DD"` (`transaction_repository.py:35-37`, `data_processors.py:258-260,341-343`).
- [ ] Mixed `transactionDate` encodings (space-separated via deprecated sqlite3 adapter at `data_processors.py:489` vs `T`-separated from migrations/sample data) — unify storage format and stop relying on the deprecated datetime adapter (breaks on future Python).
- [ ] Naive vs aware `datetime.now()` mixed throughout (`banks.py:90`, `sync_service.py:57` vs `sync_service.py:116,311`); naive/aware comparison `TypeError` is swallowed with `continue`, silently skipping expiry notifications (`sync_service.py:321-346`).
- [ ] Frontend date off-by-one: `toISOString()` on local dates shifts ranges a day in UTC+ zones (`DateRangePicker.tsx:56-65`, `lib/timePeriods.ts:8`); `formatDate` parses UTC, renders local (`lib/utils.ts:18-25`). Use local `date-fns format(d, "yyyy-MM-dd")`.
- [ ] Sync completion doesn't invalidate `["transactions"]`, `["balances"]`, `["accounts"]`, stats queries (`Sync.tsx:112-130`); running sync never polls (no `refetchInterval`) so the spinner runs forever (`Sync.tsx:102-110`).
- [ ] `Transaction` type drift: `creditor_name`, `debtor_name`, `reference`, `booking_date`, `value_date`, `created_at`, `updated_at` don't exist in backend responses (`types/api.ts:102-126` vs `leggen/api/models/accounts.py:46-66`) — the From/To/Ref/Booked UI in `TransactionsTable.tsx` is dead. Expose fields server-side (they're in `raw_transaction`) or prune type + UI.
- [ ] Multi-currency sums are meaningless: sidebar sums `balances[0].amount` across currencies as EUR (`AppSidebar.tsx:62-66`); analytics hard-codes `€` (`analytics.tsx:116-140` + chart components); backend stats sum mixed currencies (`routes/transactions.py:135`). Group by currency at minimum.
- [ ] Scheduler cron `day_of_week` mismatch: standard cron 0=Sunday vs APScheduler 0=Monday (`background/scheduler.py:82-89`).
- [ ] Invalid cron aborts `start()` before `scheduler.start()`, then `reschedule_sync` no-ops forever (`scheduler.py:28-30,50`).
- [ ] Notification send errors re-raise inside the per-account sync loop, marking a successful sync as failed and firing a sync-failure alert (`sync_service.py:189-192`, `notification_service.py:166,179`).
- [ ] `NotificationService`/`EnableBankingService` cache config at construction; settings changes ignored until restart (`notification_service.py:10-12`, `enablebanking_service.py:16`, `utils/config.py:125`).
- [ ] `/notifications` route renders the Sync component (`frontend/src/routes/notifications.tsx:2-6`); PWA shortcut points to nonexistent `/transactions` (`vite.config.ts:32`); no `notFoundComponent`; `ErrorBoundary.tsx` exists but is never mounted.
- [ ] `per_page=0` → ZeroDivisionError, negatives accepted (`routes/transactions.py:21,116` — add `ge=1`); non-numeric `category_id` → 500 via `int()` (`transaction_repository.py:56`).
- [ ] Transaction matching both case-insensitive and case-sensitive filter lists is notified twice (`notification_service.py:104-130`).
- [ ] Blocking I/O in async paths: `requests` in Telegram/Discord senders, boto3 in `BackupService`, sync sqlite3 in every route — event loop stalls on slow calls. Consolidate on httpx (drops the `requests` dep) and thread off DB/S3 work.
- [ ] Backup uploads the live DB file without the sqlite backup API (torn snapshot during concurrent sync); restore accepts any S3 key and swaps the DB under a running server; `temp_path.replace()` fails across filesystems in Docker (`backup_service.py:106,178-185`).
- [ ] `banks/callback` never verifies the `state` param (`enablebanking_service.py:92`, `routes/banks.py:71`).
- [ ] Client-side global filter in `TransactionsTable` uses the un-debounced term over server-paginated data → visible rows disagree with stats bar; column sorting only sorts the current page (`TransactionsTable.tsx:362-405,480`). Drop client filtering/sorting or move server-side.
- [ ] Expiry notifications: expired sessions re-notify every sync forever; 7/3/1-day warnings only fire on exact-day hits (`sync_service.py:302-347`). Add notification state/dedup.

## 🟡 Half-implemented features

- [ ] `SyncRequest.account_ids` accepted but ignored — per-account sync doesn't exist (`api/models/sync.py:30`, `routes/sync.py:24`).
- [ ] `transactions_updated` always 0 — plumbed through models/DB/UI, never incremented (`sync_service.py:63,232`).
- [ ] `POST /notifications/test` ignores the user's message, sends a canned expiry notification (`notification_service.py:181-209`); Discord/Telegram test buttons give zero UI feedback (`DiscordConfigDrawer.tsx:71-77`, `TelegramConfigDrawer.tsx:73-78`).
- [ ] No scheduled S3 backups despite `enabled` flag — only manual `POST /backup/operation`; add a scheduler job.
- [ ] Settings can't be cleared: empty notification filter lists skipped on save (`routes/notifications.py:82-91`); S3 config can't be removed via API (`routes/backup.py:80-95`).
- [ ] `maximum_consent_validity` plumbed but never passed — consents hardcoded to 90 days (`enablebanking_service.py:80`, `routes/banks.py:55-60`).
- [ ] Deep-link search params (`accountId`/`startDate`/`endDate`) declared but never read (`routes/index.tsx:6-10`).
- [ ] Backup restore exists in API but has no UI.
- [ ] `GET /auth/status` always returns `auth_enabled: true`; frontend caller is dead (`routes/auth.py:46-49`, `api.ts:487`).
- [ ] `[database] sqlite` config section is a no-op (`utils/config.py:200`); remove from config + example.
- [ ] `generate_sample_db --force` doesn't overwrite (old rows persist); printed instructions use invalid `leggen server --database X` ordering (`generate_sample_db.py:662-679`).

## 🧹 Dead code & simplification

- [x] Delete dead frontend files (grep-verified, zero imports): `AccountsOverview.tsx`, `AccountSettings.tsx` (false "coming soon" claims), `Notifications.tsx` + `NotificationsSkeleton.tsx`, `ui/tabs.tsx`, `ui/progress.tsx`, `ui/pagination.tsx`, `App.css`, `assets/react.svg`. Wire up `ErrorBoundary.tsx` instead of deleting. Fixed: files deleted; `ErrorBoundary` now wraps both `Outlet`s in `__root.tsx`.
- [x] Remove unused npm deps: `@dnd-kit/*` (×4, also pinned into `vendor-table` chunk in `vite.config.ts:123-129`), `zod`, `next-themes`, `@radix-ui/react-toggle`, `react-toggle-group`, `react-tabs`, `react-progress`, `@tanstack/router-cli`; move `tailwindcss`/`postcss`/`autoprefixer` to devDependencies. Fixed: 11 packages removed, build verified.
- [x] Delete dead backend code: `utils/disk.py`; `TransactionRepository.get_account_summary`; `SessionRepository.get_all_account_ids` (kept the inline version in `sync_service.py` — it also builds the account→session map, which the repo method doesn't) and `.get_session`; `CategoryRepository.get_transaction_category`; `LeggenAPIClient.get_transaction_stats`; `Config.update_config`; `is_sqlite_enabled`; dead models `NotificationHistory`, `BackupInfo`; dead index `idx_transactions_internal_id` (creation removed; existing DBs keep the harmless index); stale GoCardless-era `__pycache__` artifacts. Also deleted the equally-dead `EnableBankingService.get_session`.
- [x] Dedup DDL: table creation duplicated across repositories, `migration_repository.py:524,679`, and `generate_sample_db.py:110-233` (already drifted — missing `logo` column, no sessions/sync_operations tables). Fixed: lifespan now runs `ensure_tables()` before migrations, making the three pure table-creation migrations (sync_operations, sessions, categories) redundant — deleted; `generate_sample_db` reuses `ensure_tables()` via `path_manager.set_database_path()`, so sample DBs get the full current schema.
- [x] Fix layering inversion: `category_repository.py:6` imports from services. Fixed: `services/categorizer.py` was a pure utility — moved to `leggen/utils/keywords.py`.
- [x] Reuse `httpx.AsyncClient` and cache the 1-hour EnableBanking JWT instead of per-request creation (`enablebanking_service.py:48,56`); cache the `/aspsps` list instead of refetching per account per sync (`data_processors.py:63-78` — also stop overwriting stored logo with NULL on fetch failure). Fixed: shared lazy client, JWT cached until 60s before expiry, `/aspsps` cached per country (1h TTL), and `AccountRepository.persist` preserves the stored logo the same way it preserves `display_name`.
- [x] Pydantic v2 cleanup: replace `.dict()` calls (`utils/config.py:46,82,184`) and v1-style `class Config: json_encoders` in API models. Fixed: `.dict()` calls were already gone; removed all nine `json_encoders` Config blocks (v2 serializes datetime to ISO by default — deprecation warnings in pytest dropped from 31 to 11).

## 🎨 Consistency

- [ ] Dark-mode pass over hard-coded colors: `ActiveFilterChips.tsx:117,122`, `AccountCombobox.tsx:85,113`, transaction icon chips (`TransactionsTable.tsx:243-244,587-589`), `Accounts.tsx:329`; charts should use `--chart-1..5` CSS vars (`BalanceChart.tsx:119`, `TransactionDistribution.tsx:57`).
- [ ] Unify confirmation UX (native `confirm()` vs `AlertDialog` vs `Dialog`), loading states (skeleton/spinner/hand-rolled pulse; add `placeholderData` to analytics), and error feedback (toasts vs silent `console.error` vs inline alerts; toast backend `detail`, not Axios `error.message`).
- [ ] Replace hand-rolled `RawTransactionModal` with Radix Dialog (no focus trap/Escape/aria today).
- [ ] Dedup `getStatusIndicator` (×3) and `getBankName`/`getAccountDisplayName` (×2 in analytics).
- [ ] CLI: exit non-zero on failure everywhere (currently `return` after catch → exit 0); `bank/delete.py` missing health check and error handling; unify stderr `error()` vs stdout `click.echo`.
- [ ] API error conventions: stop embedding `str(e)` in 500 bodies (path/SQL leakage — categories routes already sanitize, copy that); `POST /sync` should return 409 not 500 for "already running"; unify `limit`/`offset` vs `page`/`per_page`.
- [ ] Fix wrong env var in error message: `LEGGEN_CONFIG` → `LEGGEN_CONFIG_FILE` (`utils/config.py:191`).
- [ ] `NotificationService.active` is the real on/off signal; `Settings.tsx:305-320` derives status from `enabled && configured` — "Needs Configuration" state unreachable.
- [ ] Naming drift (larger effort, needs migration): `institution_id` stores ASPSP name, `balances.bank`, camelCase `transactions` columns vs snake_case elsewhere, `internalTransactionId` holding `entry_reference`.
- [ ] Balances table: add `UNIQUE(account_id, type, timestamp)` or skip-if-unchanged dedup — currently unbounded append growth; the `IntegrityError` handler at `balance_repository.py:67` is dead code.
- [ ] Pending→booked reconciliation: pending rows keyed by `entry_reference` are never removed when the booked version arrives (`data_processors.py:477-481`).

## 🔧 CI / tooling

- [ ] Add `ruff check` + `mypy` to CI (currently pytest only, `.github/workflows/ci.yml`).
- [ ] Gate `release.yml` on tests (currently any tag ships to PyPI/Docker).
- [ ] `frontend/Dockerfile`: `npm ci` instead of `npm i`; bump Node 20 (EOL) base image and CI `node-version`.
- [ ] Add tests for the riskiest untested code: `migration_repository.py` (840 lines, zero coverage), `data_processors.py`, `enablebanking_service.py`, repositories, CLI commands (the `cli` marker exists, unused — would have caught the bank-group break).
- [ ] Add a frontend test runner (vitest) — currently zero frontend tests.
- [ ] Backend Dockerfile: non-root `USER`; drop the redundant dev-group `uv sync` layer.
- [ ] Fix `.dockerignore` entry `docker-compose.dev.yml` → `compose.dev.yml`.
- [ ] Dependency bumps to plan: Tailwind 3→4 (real migration), recharts 2→3, zod 3→4 (or remove — currently unused); revisit the `serialize-javascript` override after bumping.
- [ ] Docs: add S3 backup to README features; fix frontend/README "Node 18+" (Vite 7 needs 20.19+); fix `frontend/package.json` version `0.0.0`.

## ✨ New feature ideas (not yet in TASKS.md)

- [ ] Scheduled S3 backups (also listed under half-implemented — the flag exists, make it real).
- [ ] Net-worth / balance-over-time dashboard on the overview page — `/balances/history` and per-sync snapshots already exist.
- [ ] Data-driven bank names/logos in analytics — accounts table stores `logo`; kills the hard-coded 3-bank map (`TransactionDistribution.tsx:41`).
- [ ] Pending-transaction filter/visual distinction — `transactionStatus` is stored and counted but not surfaced.
- [ ] Per-currency stats grouping (prerequisite for meaningful totals with multi-currency accounts).
- [ ] Notification history table — persists sent notifications, gives `/notifications` a purpose (overlaps TASKS.md "Stale route" item).

Already tracked in [TASKS.md](TASKS.md): budgets, recurring detection, rules, CSV export, onboarding, transaction detail view, keyboard nav, multi-select, migrations framework, error consistency, notes/attachments.

## 🗣️ To be discussed later

- [ ] Account deletion is really an "archive" feature — decide the semantics and make code/UX coherent. Accounts are keyed by IBAN on purpose (stable identity across sessions, `sync_service.py:135`), so a "deleted" account under an active bank connection comes back on the next sync — that's intended. What's incoherent today: sync overwrites the `DELETED` status back to `READY` (`sync_service.py:141`), losing the archive flag; `delete_data=true` purges history that sync then partially re-imports (last 30 days), leaving a permanent hole; the "skip deleted accounts" block (`sync_service.py:103-109`) compares IBANs to session UIDs and is dead code; and there's no unarchive action or archived-accounts filter (`GET /accounts` returns them by default, `account_repository.py:93`). Proposed shape: rename to Archive in UI/API, sync preserves the archived status, drop `delete_data` and the dead exclusion block, hide archived accounts from default views with a toggle, add unarchive. Open question: should archived accounts keep syncing in the background (recommended) or be skipped?
