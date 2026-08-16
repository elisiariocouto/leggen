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
