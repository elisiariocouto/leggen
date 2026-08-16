import { createFileRoute } from "@tanstack/react-router";
import TransactionsTable from "../components/TransactionsTable";
import {
  asISODate,
  asPositiveInt,
  asTrimmedString,
} from "../lib/searchParams";

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
