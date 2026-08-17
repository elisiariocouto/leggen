# card

2026-08-17 — golden pair via CLI (base-nova) — customization replayed onto the new file.

## Changed

- `src/components/ui/card.tsx` — replaced with the base-nova variant, which
  swaps the border for `ring-1 ring-foreground/10`, moves to `rounded-xl`, and
  introduces a `--card-spacing` variable plus a `size="sm"` variant and a new
  `CardAction` slot.
- **Replayed local change**: `CardTitle` stays an `<h3>` rather than nova's
  `<div>`. Card titles are section headings here and belong in the heading
  outline for screen readers; the typography classes are nova's.

Leftover scan: clean.

## Left alone

The previous `rounded-lg` / `shadow-xs` treatment was deliberately dropped in
favour of nova's ring-based card, since adopting the style is the point of
this migration.

## Behavior changes

- Cards read as ringed rather than bordered, with a slightly larger radius.
- `CardTitle` is `text-base` where the local version was `text-2xl`; headings
  inside cards are noticeably smaller.

## Verify by hand

- Open Settings and Analytics and scan the card headers — confirm the smaller
  title size is acceptable, since it affects every card in the app.
- Check the stat tiles on Analytics still align in their grid.
