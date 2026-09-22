import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api";
import { queryKeys } from "../lib/queryKeys";

/**
 * The queries read by more than one component, declared once.
 *
 * Every call site used to spell out its own key, fetcher and options, so the
 * same cache entry could be read with different settings depending on which
 * component happened to mount first. Queries used by a single component stay
 * inline where they are used.
 */

interface QueryToggle {
  enabled?: boolean;
}

export function useCategories({ enabled }: QueryToggle = {}) {
  return useQuery({
    queryKey: queryKeys.categories,
    queryFn: apiClient.getCategories,
    enabled,
  });
}

export function useAccounts({ enabled }: QueryToggle = {}) {
  return useQuery({
    queryKey: queryKeys.accounts,
    queryFn: apiClient.getAccounts,
    enabled,
  });
}

/**
 * The category-by-month pivot behind most of the analytics page. Keeping the
 * previous window's data while the next one loads stops every panel reading
 * it from collapsing to a skeleton when the period changes.
 */
export function useSpendingByCategory(
  dateFrom: string,
  dateTo: string,
  accountId?: string,
  { enabled }: QueryToggle = {},
) {
  return useQuery({
    queryKey: queryKeys.spendingByCategory(dateFrom, dateTo, accountId),
    queryFn: () =>
      apiClient.getSpendingByCategory({ dateFrom, dateTo, accountId }),
    placeholderData: (previousData) => previousData,
    enabled,
  });
}

/**
 * Rule names also label every rule-assigned category badge, so a page of
 * transactions mounts this many times at once. The stale time keeps each new
 * badge reading the cache instead of refetching the list; rule edits
 * invalidate it explicitly.
 */
export function useCategoryRules() {
  return useQuery({
    queryKey: queryKeys.categoryRules,
    queryFn: apiClient.getCategoryRules,
    staleTime: 60_000,
  });
}
