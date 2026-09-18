import { endOfMonth, format, parse, startOfMonth } from "date-fns";

/**
 * Month-axis helpers shared by the analytics charts and tables. Months are
 * the "YYYY-MM" strings the API groups by.
 */

/** "2025-09" reads as "Sep 2025" (long) or "Sep" (short). */
export function monthLabel(
  month: string,
  style: "long" | "short" = "long",
): string {
  try {
    const date = parse(month, "yyyy-MM", new Date());
    return format(date, style === "long" ? "MMM yyyy" : "MMM");
  } catch {
    return month;
  }
}

/**
 * Whether the window [dateFrom, dateTo] covers every day of `month`. A
 * window that starts or ends mid-month yields a partial first or last
 * column, which must not be mistaken for a quiet month.
 */
export function isCompleteMonth(
  month: string,
  dateFrom: string,
  dateTo: string,
): boolean {
  try {
    const date = parse(month, "yyyy-MM", new Date());
    return (
      format(startOfMonth(date), "yyyy-MM-dd") >= dateFrom &&
      format(endOfMonth(date), "yyyy-MM-dd") <= dateTo
    );
  } catch {
    return false;
  }
}

/** Median, or null for an empty list. Robust to one-off spikes, unlike the mean. */
export function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = sorted.length >> 1;
  return sorted.length % 2 === 1
    ? sorted[mid]
    : (sorted[mid - 1] + sorted[mid]) / 2;
}
