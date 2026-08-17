# theme

2026-08-17 — golden pair via CLI (base-nova) — color tokens converted to oklch; palette unchanged.

## Changed

- `src/index.css` — every color token converted from bare HSL channels
  (`--primary: 219 91% 46%`) to full oklch values (`oklch(0.5057 0.2214
  261.91)`), and `@theme` switched from `hsl(var(--x))` wrappers to inline
  `var(--x)`. Base UI wrappers consume tokens directly and mix them with
  `color-mix(in oklch, ...)`, which silently yields wrong colors against the
  old format. Conversion was verified to round-trip exactly: `--primary`,
  `--destructive`, `--positive` and `--muted` all reproduce their original
  sRGB values bit-for-bit, so the palette is visually unchanged.
- `src/index.css` — added `@import 'shadcn/tailwind.css'`, which supplies the
  `data-open` / `data-closed` / `data-checked` / `data-disabled` custom
  variants that Base UI components rely on. It contains no color tokens, so
  the brand palette stays fully local to this repo.
- `src/index.css` — `*` now also carries `outline-ring/50`, per the nova base
  layer.
- `src/lib/chartColors.ts` — doc comment corrected; it described the tokens as
  "raw HSL triplets". The `var(--color-chart-*)` references it exports are
  unaffected and still resolve.

Leftover scan: `grep -n "hsl(var" src/` is clean.

## Left alone

The custom `--positive` / `--negative` / `--positive-muted` /
`--negative-muted` money-direction pair and the `--sidebar-*` set were
converted in place rather than replaced with nova values, so the semantic
colors keep their meaning.

## Behavior changes

None. Colors are numerically identical after conversion.

## Verify by hand

- Toggle light → dark → system: all three render, no flash of unstyled color.
- Check an income row (green) and an expense row (red) in the transactions
  table, and the trend icons behind them.
- Open Analytics: the five chart series colors and the grid/axis chrome
  should look exactly as before.
