# button

2026-08-17 — golden pair via CLI (base-nova) — pristine wrapper, taken wholesale.

## Changed

- `src/components/ui/button.tsx` — replaced with the base-nova variant. Now
  wraps the real `@base-ui/react/button` primitive instead of a Radix `Slot`;
  `asChild` is gone in favour of Base UI's `render` prop.

Leftover scan: clean.

## Left alone

No call site passed `asChild` to `Button` itself — every `asChild` in the app
was on a *trigger* wrapping a Button — so no consumer needed changing for this
component.

## Behavior changes

- Sizes shift: nova's `default` is `h-8` (was `h-9`), `sm` is `h-7` (was
  `h-8`). 25 `size="sm"` and 13 `size="icon"` call sites are affected.
- `destructive` flips from a solid red fill with white text to a tinted
  `bg-destructive/10` with destructive-colored text. 5 call sites.
- Focus ring widens from `ring-1` to `ring-3`; hover moves from `bg-accent` to
  `bg-muted`.
- Buttons gain `active:translate-y-px` press feedback.

## Verify by hand

- Look at the 5 destructive buttons (delete account, delete category): they
  are now tinted rather than solid. Confirm that reads as destructive enough.
- Tab to any button: the focus ring is thicker than before.
- Check the icon buttons in the Accounts table still line up with their rows.
