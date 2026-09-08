/**
 * Coercion helpers for route `validateSearch`.
 *
 * URL search params are user input: they arrive from bookmarks, shared
 * links and hand-editing. Each helper returns `undefined` for anything it
 * does not recognise, so a malformed param falls back to the route's
 * default instead of reaching the API.
 */

export function asTrimmedString(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  const trimmed = value.trim();
  return trimmed === "" ? undefined : trimmed;
}

export function asPositiveInt(value: unknown): number | undefined {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1) return undefined;
  return parsed;
}

// Only the format the app itself emits (yyyy-MM-dd) is accepted.
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

export function asISODate(value: unknown): string | undefined {
  const text = asTrimmedString(value);
  if (!text || !ISO_DATE.test(text)) return undefined;
  // Rejects impossible dates. Date() silently rolls these over rather than
  // failing — 2026-02-31 becomes March 3 — so the only reliable check is
  // whether the parsed date formats back to the string we were given.
  const parsed = new Date(`${text}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return undefined;
  const roundTrip = `${parsed.getFullYear()}-${String(
    parsed.getMonth() + 1,
  ).padStart(2, "0")}-${String(parsed.getDate()).padStart(2, "0")}`;
  return roundTrip === text ? text : undefined;
}

/**
 * Transaction status filter. Only the two values the API accepts get
 * through — anything else falls back to the unfiltered view rather than
 * reaching the backend and coming back a 422.
 */
const TRANSACTION_STATUSES = ["booked", "pending"] as const;

export type TransactionStatusFilter = (typeof TRANSACTION_STATUSES)[number];

export function asTransactionStatus(
  value: unknown,
): TransactionStatusFilter | undefined {
  const text = asTrimmedString(value)?.toLowerCase();
  return TRANSACTION_STATUSES.find((status) => status === text);
}

/**
 * Sort field and direction for the transaction list.
 *
 * The values mirror the API's own enums; anything else falls back to the
 * default ordering rather than reaching the backend and coming back a 422.
 */
const TRANSACTION_SORT_FIELDS = ["date", "amount", "description"] as const;
const SORT_DIRECTIONS = ["asc", "desc"] as const;

export type TransactionSortField = (typeof TRANSACTION_SORT_FIELDS)[number];
export type SortDirection = (typeof SORT_DIRECTIONS)[number];

export function asTransactionSortField(
  value: unknown,
): TransactionSortField | undefined {
  const text = asTrimmedString(value)?.toLowerCase();
  return TRANSACTION_SORT_FIELDS.find((field) => field === text);
}

export function asSortDirection(value: unknown): SortDirection | undefined {
  const text = asTrimmedString(value)?.toLowerCase();
  return SORT_DIRECTIONS.find((direction) => direction === text);
}

/**
 * A transaction magnitude bound. Unlike `asPositiveInt` this accepts 0 and
 * decimals — amounts are money, and "from 0" is a meaningful lower bound —
 * but rejects negatives, since a magnitude is a size and not a signed value.
 */
export function asNonNegativeNumber(value: unknown): number | undefined {
  // Both shapes arrive here: a string when the param is read off the URL,
  // and a number once the router has already parsed it (or when a handler
  // writes one back). `asTrimmedString` rejects the latter, so it cannot be
  // the front of this check.
  if (typeof value === "number") {
    return Number.isFinite(value) && value >= 0 ? value : undefined;
  }
  const text = asTrimmedString(value);
  if (text === undefined) return undefined;
  const parsed = Number(text);
  if (!Number.isFinite(parsed) || parsed < 0) return undefined;
  return parsed;
}
