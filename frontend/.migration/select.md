# select

2026-08-17 — golden pair via CLI (base-nova) — pristine wrapper plus a local null-narrowing shim.

## Changed

- `src/components/ui/select.tsx` — replaced with the base-nova variant.
- Added a local `Select` wrapper around `SelectPrimitive.Root`. Base UI widens
  `onValueChange` to `(value: string | null, eventDetails)` because a select
  can be cleared programmatically. None of this app's selects are clearable —
  each is bound to a required field — so the wrapper drops the null case in
  one place rather than forcing four call sites to handle a value they can
  never receive. `onValueChange` is destructured out before `{...props}`
  spreads, so the handler cannot be overridden.

Leftover scan: clean.

## Left alone

The four call sites (`AddBankAccountDrawer` ×3, `DateRangePicker` ×1) keep
their existing `(value: string) => void` handlers unchanged.

## Behavior changes

- The trigger is now a `<button>` with an adjacent hidden input for form
  participation.
- Base UI's select popup positions via a Positioner; `side="top"` on the
  rows-per-page select still resolves correctly.

## Verify by hand

- Change "Rows per page" at the bottom of the transactions table: the value
  applies and the URL gains `?perPage=N`.
- Open the country select inside the Add Account drawer — a select nested in a
  vaul drawer is the riskiest combination; confirm the list opens above the
  drawer and picking a value populates the bank list.
- Keyboard: open a select, type the first letters of an option, press Enter.
