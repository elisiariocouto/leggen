# project

2026-08-17 — whole-project migration from Radix UI (`new-york`) to Base UI (`base-nova`).

## Outcome

Every Radix-backed wrapper now uses `@base-ui/react` 1.7.0. All twelve
`@radix-ui/*` direct dependencies were removed. `components.json` was flipped
from `new-york` to `base-nova`, so future `shadcn add` delivers matching
variants (`shadcn info` reports `base: base`).

Because `base-new-york` does not exist, this was necessarily also a restyle:
`base-nova` was chosen deliberately over vega/lyra/mira after comparing all
four.

## Dependency swap

Removed: `@radix-ui/react-{alert-dialog,avatar,checkbox,dialog,dropdown-menu,label,popover,select,separator,slot,switch,tooltip}`.
Added: `@base-ui/react`.

Radix remains in `package-lock.json` transitively — `cmdk` and `vaul` each
bundle `@radix-ui/react-dialog` internally. That is expected and not ours to
remove.

`command.tsx` imported a Radix *type* (`DialogProps`); it now derives its
props from this project's own `Dialog`, with `children` narrowed to
`ReactNode` because Base UI's Dialog also accepts a render function that cmdk
cannot take.

## App-code sweep

20 `asChild` call sites converted to `render` (18 mechanically, 2 by hand: a
ternary child in `CategoryBadge` and an expression child in the sidebar).
Drawer triggers were deliberately left on `asChild` — vaul is not Radix.

Four `Select` handlers were left unchanged; the null-widening was absorbed in
the wrapper instead.

## Verification

- `tsc -b --noEmit`, `eslint`, and `vite build` all clean, matching the
  pre-migration baseline.
- The app was run against the sample database and driven through
  Transactions, Analytics, Accounts and Settings in light, dark and mobile
  layouts. Select, DropdownMenu, Popover, Checkbox, Dialog, Sheet and the
  cmdk Command palette were each exercised. A Base UI Select nested inside a
  vaul Drawer was checked specifically.
- One regression was found this way and fixed: unpadded `SheetContent` (see
  `overlays.md`). It did not surface in typecheck or build.

## Known issues, not fixed

- **Pre-existing horizontal overflow.** `SidebarInset` carries
  `w-full flex-1`, so `main` computes 80px wider than the viewport
  (`scrollWidth` 1280 vs `clientWidth` 1200 at 1200px). The classes are
  byte-identical between the old new-york file and the nova one, so this is
  upstream shadcn behavior that predates the migration. Left alone as out of
  scope; worth a follow-up.
- **vaul `aria-hidden` warning** on drawer open — transient, vaul-internal.
  See `overlays.md`.
- **Non-Radix components keep their old styling.** `command`, `drawer`,
  `sonner` and `calendar` were correctly not migrated, but they now sit
  visually alongside base-nova components. Restyling them is the natural
  follow-up.

## Remaining

0 wrappers remain on Radix.
