# overlays

2026-08-17 — golden pair via CLI (base-nova) — dialog, alert-dialog, sheet, popover, tooltip, dropdown-menu.

Covers the five overlay families together: they share one structural change
and one consumer sweep.

## Changed

- `src/components/ui/{dialog,alert-dialog,sheet,popover,tooltip,dropdown-menu}.tsx`
  — replaced with base-nova variants. Overlays restructure from Radix's
  `Portal > Overlay > Content` into Base UI's
  `Portal > Backdrop > Positioner > Popup`. `DialogOverlay` is now backed by
  `Dialog.Backdrop`.
- Registry artifacts were normalized out of every fetched file before install:
  `IconPlaceholder` tokens were resolved to the matching lucide icons (the
  project's configured icon library), the `@/ui/` and `@/registry/base-nova/`
  aliases were rewritten to this project's aliases, and the placeholder
  `cn-font-heading` class — which is not a real utility and would have been
  dead — was dropped.
- 18 consumer call sites converted from `asChild` to `render` across
  `Accounts.tsx`, `AppSidebar.tsx`, `CategoryManager.tsx`, `Settings.tsx`,
  `SiteHeader.tsx`, `Sync.tsx`, and the three `filters/*` comboboxes.
- `CategoryBadge.tsx:159` — hand-converted; its trigger child is a ternary
  rather than a single element, so the conditional moved inside `render={...}`.
- `TransactionDetail.tsx:350` — **regression fix**. nova's `SheetContent`
  ships no padding of its own (new-york's had `p-6`); nova expects
  `SheetHeader`/`SheetFooter` to pad themselves. This component puts raw
  content in the sheet body, so it rendered flush to both edges. The body div
  now carries `px-4 pb-4`. Caught by driving the app, not by typecheck.

Leftover scan: `grep -n "radix-ui\|@radix-ui\|IconPlaceholder"` is clean
across all six files.

## Left alone

`command.tsx` (cmdk), `drawer.tsx` (vaul), `sonner.tsx` (sonner) and
`calendar.tsx` (react-day-picker) are not Radix and were not migrated. They
keep their previous styling and will read slightly differently next to the
base-nova components until restyled.

`label.tsx` and `scroll-area.tsx` were already de-Radixed in this repo — a
native `<label>` and a plain overflow div. Base UI has no Label primitive, so
both are already in their target state and were left untouched.

Dialog and AlertDialog content keep `p-4` in nova, and every `PopoverContent`
call site passes an explicit `p-0`, so Sheet was the only padding casualty.

## Behavior changes

- Base UI renders a hidden form input alongside Select and Checkbox for form
  participation. The accessibility tree therefore shows two nodes per control;
  they stay in sync and this is expected, not a duplicate control.
- Opening a vaul Drawer logs a transient `aria-hidden` warning: vaul marks the
  background `<main>` hidden while the trigger still holds focus, before
  moving focus into the drawer. Measured 400ms after open, focus is correctly
  outside the hidden region. This originates in vaul's own code, not in the
  migration, and is left unpatched.

## Verify by hand

- Open it, press Escape: it closes and focus returns to the trigger.
- Tab through the content: focus stays trapped inside while open.
- Click the backdrop: it dismisses (or intentionally does not).
- Re-open twice in a row: no stale content, no double backdrop.
- Tooltips: hover an icon button in Accounts — check the delay still feels
  right and the arrow points at the trigger.
- Dropdown: open the user menu in the sidebar footer, arrow-key through it,
  type-ahead a letter.
- Sheet: open a transaction's detail panel and confirm nothing is clipped at
  the right edge.
