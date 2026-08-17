# sidebar

2026-08-17 — golden pair via CLI (base-nova) — customization replayed onto the new file.

## Changed

- `src/components/ui/sidebar.tsx` — replaced with the base-nova variant.
- **Replayed local fix**: `SidebarMenuSkeleton` keeps this repo's
  deterministic width. nova still ships `Math.floor(Math.random() * 40) + 50`
  (line 616 of the registry file), which is impure and produces a different
  width on every render. The local version derives the width from
  `React.useId()` via a stable hash, and that implementation plus its
  explanatory comment were carried onto the new file.
- Fixed a stale `hsl(var(--sidebar-border))` in the old file's
  `SidebarMenuButton` outline variant. With tokens now holding `oklch(...)`
  values, wrapping one in `hsl()` is invalid and the border would have
  silently vanished. The nova replacement does not use that construct.
- `AppSidebar.tsx:91,114` — two `SidebarMenuButton asChild` wrapping
  TanStack Router `<Link>` converted to `render`.

Leftover scan: clean.

## Left alone

The 404-line diff against the radix golden was almost entirely Tailwind v4
codemod drift (`w-[--x]` → `w-(--x)`, `theme(spacing.4)` → `--spacing(4)`) and
prettier formatting, not customization. Only the skeleton-width fix was a real
local change, and it was preserved.

## Behavior changes

None intended beyond nova's visual treatment.

## Verify by hand

- Collapse and expand the sidebar (the toggle, and Cmd/Ctrl-B): the icon-rail
  state and the content gap both animate correctly.
- Narrow the window below the mobile breakpoint: the sidebar becomes a Sheet
  that slides over the content.
- Hover a collapsed rail item: its tooltip appears.
- Reload: the expanded/collapsed state persists via the cookie.
