import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Account } from "../types/api";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(
  amount: number,
  currency: string = "EUR",
): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(amount);
}

/**
 * Most common currency in a list. Used to pick the one currency a mixed
 * dataset is aggregated/displayed in (summing across currencies is
 * meaningless).
 */
export function dominantCurrency(
  currencies: Array<string | null | undefined>,
  fallback: string = "EUR",
): string {
  const counts = new Map<string, number>();
  for (const currency of currencies) {
    if (!currency) continue;
    counts.set(currency, (counts.get(currency) || 0) + 1);
  }
  let best = fallback;
  let bestCount = 0;
  for (const [currency, count] of counts) {
    if (count > bestCount) {
      best = currency;
      bestCount = count;
    }
  }
  return best;
}

export function formatDate(dateString: string): string {
  // Parse the calendar date directly — new Date("YYYY-MM-DD") interprets a
  // date-only string as UTC midnight, which renders as the previous day in
  // zones west of Greenwich.
  const [datePart] = dateString.split(/[T ]/);
  const [year, month, day] = datePart.split("-").map(Number);
  const date = new Date(year, (month || 1) - 1, day || 1);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * A moment in time, such as a sync or a backup, with its time of day in the
 * viewer's zone. `formatDate` drops the time, which is right for booking
 * dates but not for these.
 */
export function formatDateTime(timestamp: string): string {
  return new Date(timestamp).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

/** The name an account is shown under: the user's label, then the bank's. */
export function accountLabel(account: Account): string {
  return account.display_name || account.name || "Unnamed Account";
}
