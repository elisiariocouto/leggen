## UI/UX Improvements

- [x] Transaction search/filter improvements - The current stats (income, expenses, net) are calculated from the current page only, not the full filtered result set. This is misleading — a user filtering by "Groceries" would expect to see total grocery spending, not just page 1's total.
- [ ] Empty states & onboarding - When a user first opens the app with no bank connections, there's no guided onboarding flow. A first-run wizard or prominent call-to-action on the dashboard would help.
- [ ] Transaction detail view - Currently you can only see the raw JSON. A formatted transaction detail panel/drawer showing all fields cleanly (merchant info, status, dates, category history) would be much more useful.
- [ ] Keyboard navigation - No keyboard shortcuts for common actions (j/k to move between transactions, c to categorize, / to search). Power users managing hundreds of transactions would benefit greatly.
- [ ] Multi-select transactions - Currently bulk operations only work by description match. Being able to select multiple transactions with checkboxes and then bulk-categorize, export, or tag them would be more flexible.

---

## Features — Financial

- [ ] Budget tracking - Define monthly/weekly budgets per category, with progress bars and alerts when nearing limits. This is arguably the #1 missing feature for a personal finance tool.

- [ ] Recurring transaction detection - Automatically detect subscriptions and recurring payments (Netflix, rent, salary) by analyzing patterns. Show them in a dedicated view with expected upcoming charges.

- [ ] Spending rules/automation - Auto-categorize transactions based on user-defined rules (e.g., "if description contains 'LIDL' → Groceries"). Currently only keyword learning exists, but explicit rules would give users more control.

- [ ] CSV/data export - No export functionality exists. Users should be able to export transactions as CSV/OFX for tax purposes or migration.

---

## Features — Technical

- [ ] Database migrations system - The codebase has ad-hoc migration functions scattered in the migration repository. A proper migration framework (like Alembic or even a simple versioned migration system) would prevent schema drift issues.
- [ ] API authentication - No auth at all currently. Even for a self-hosted app, adding optional basic auth or API keys would prevent accidental exposure.

---

## Code Quality & Developer Experience

- [ ] API error consistency - Some endpoints catch generic Exception, and error response formats vary. A unified error response schema would improve the frontend's ability to show meaningful error messages.
- [ ] Stale route: /notifications - This route exists but renders the Sync component. It should either be removed or properly implemented as a notification history/inbox view (which would actually be a nice feature — showing a log of sent notifications). A log of all sent notifications (Discord/Telegram messages) with their content and delivery status.

---
## Nice-to-haves

- [ ] Transaction notes/attachments - Let users add personal notes or attach receipt photos to transactions.
