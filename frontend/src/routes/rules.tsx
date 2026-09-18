import { createFileRoute } from "@tanstack/react-router";
import CategoryRules from "../components/CategoryRules";
import { asTrimmedString } from "../lib/searchParams";

/**
 * `merchant` opens the editor with a rule for that merchant drafted, which
 * is how the analytics page hands over an uncategorized merchant.
 */
export interface RulesSearch {
  merchant?: string;
}

export const Route = createFileRoute("/rules")({
  component: CategoryRules,
  validateSearch: (search: Record<string, unknown>): RulesSearch => ({
    merchant: asTrimmedString(search.merchant),
  }),
});
