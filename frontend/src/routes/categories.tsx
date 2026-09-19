import { createFileRoute } from "@tanstack/react-router";
import CategoryRules from "../components/CategoryRules";
import { asTrimmedString } from "../lib/searchParams";

/**
 * `merchant` opens the rule editor with a rule for that merchant drafted,
 * which is how the home page hands over an uncategorized merchant.
 */
export interface CategoriesSearch {
  merchant?: string;
}

export const Route = createFileRoute("/categories")({
  component: CategoryRules,
  validateSearch: (search: Record<string, unknown>): CategoriesSearch => ({
    merchant: asTrimmedString(search.merchant),
  }),
});
