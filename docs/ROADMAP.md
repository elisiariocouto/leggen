# Roadmap

> Line references drift as the code moves. Verify them before starting an item —
> and re-check the claim itself, since a refactor may already have fixed it.

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
