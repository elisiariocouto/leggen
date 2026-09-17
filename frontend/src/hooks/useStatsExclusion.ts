import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
import type { Category, Transaction } from "@/types/api";

/**
 * Resolves whether a transaction counts towards statistics.
 *
 * The API stores a tri-state override on the transaction: `true`/`false`
 * decide outright, `null` inherits the category's flag. Every reader of the
 * flag needs the same resolution, so it lives here rather than at each site.
 * The categories list is already in the cache from the badge on every row.
 */
export function useStatsExclusion(transaction: Transaction) {
  const { data: categories } = useQuery<Category[]>({
    queryKey: queryKeys.categories,
    queryFn: apiClient.getCategories,
  });

  const category =
    transaction.category_id != null
      ? categories?.find((c) => c.id === transaction.category_id)
      : undefined;
  const categoryExcluded = category?.exclude_from_stats ?? false;
  const overridden = transaction.exclude_from_stats != null;

  return {
    /** What the statistics actually do with this transaction. */
    excluded: overridden ? transaction.exclude_from_stats === true : categoryExcluded,
    /** Whether the transaction carries its own flag rather than inheriting. */
    overridden,
    /** What the transaction would do if the override were cleared. */
    categoryExcluded,
    hasCategory: category !== undefined,
  };
}
