/**
 * Shared chart palette.
 *
 * Uses the `--color-chart-*` custom properties that the `@theme` block in
 * index.css maps onto the `--chart-N` oklch tokens — those resolve to real
 * colors at SVG attribute-parse time.
 *
 * Charts that color by entity (categories carry their own `category_color`)
 * use that value instead; this palette is for series that have no colour of
 * their own, so they stay consistent across charts.
 */
export const CHART_COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
] as const;

/** Palette entry for a series index, wrapping around for long series. */
export function chartColor(index: number): string {
  return CHART_COLORS[index % CHART_COLORS.length];
}

/**
 * Semantic colours for income/expense series. Kept apart from the
 * categorical palette above — these encode meaning, not identity.
 */
export const INCOME_COLOR = "var(--color-positive)";
export const EXPENSE_COLOR = "var(--color-negative)";

/** Grid and axis chrome, so every chart shares one look. */
export const CHART_GRID_COLOR = "var(--color-border)";
export const CHART_AXIS_TICK = {
  fontSize: 12,
  fill: "var(--color-muted-foreground)",
} as const;
