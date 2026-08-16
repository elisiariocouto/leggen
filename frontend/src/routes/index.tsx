import { createFileRoute } from "@tanstack/react-router";
import TransactionsTable from "../components/TransactionsTable";

/**
 * Filters and pagination live in the URL so a filtered view can be
 * bookmarked, shared, and restored by the back button.
 *
 * Every field is optional and defaults to the unfiltered view, so a bare
 * "/" stays valid and older links keep working as fields are added.
 */
export interface TransactionSearch {
  q?: string;
  account?: string;
  category?: string;
  from?: string;
  to?: string;
  page?: number;
  perPage?: number;
}

function asTrimmedString(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  const trimmed = value.trim();
  return trimmed === "" ? undefined : trimmed;
}

function asPositiveInt(value: unknown): number | undefined {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1) return undefined;
  return parsed;
}

// Only the dates the app itself emits (yyyy-MM-dd) are accepted; anything
// else is dropped rather than passed through to the API.
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

function asISODate(value: unknown): string | undefined {
  const text = asTrimmedString(value);
  return text && ISO_DATE.test(text) ? text : undefined;
}

export const Route = createFileRoute("/")({
  component: TransactionsTable,
  validateSearch: (search: Record<string, unknown>): TransactionSearch => ({
    q: asTrimmedString(search.q),
    account: asTrimmedString(search.account),
    category: asTrimmedString(search.category),
    from: asISODate(search.from),
    to: asISODate(search.to),
    page: asPositiveInt(search.page),
    perPage: asPositiveInt(search.perPage),
  }),
});
