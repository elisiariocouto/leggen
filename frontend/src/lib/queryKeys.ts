import type { QueryClient } from "@tanstack/react-query";

/**
 * Every React Query key used in the app, in one place.
 *
 * Keys used to be spelled inline at each call site, which let the same
 * endpoint acquire two spellings ("transactionStats" and
 * "transaction-stats") that cached separately — call sites then had to
 * invalidate both to avoid stale panels.
 *
 * Roots are the prefixes invalidation matches on; the functions below build
 * the fully-parameterised keys that `useQuery` reads.
 */
export const queryKeys = {
  accounts: ["accounts"] as const,
  balances: ["balances"] as const,
  historicalBalances: (dateFrom: string, dateTo: string, accountId?: string) =>
    ["balances", "history", dateFrom, dateTo, accountId] as const,

  transactions: ["transactions"] as const,
  transactionList: (params: {
    accountId: string;
    categoryId: string;
    startDate: string;
    endDate: string;
    page: number;
    perPage: number;
    search: string;
  }) => ["transactions", "list", params] as const,

  transactionStats: ["transaction-stats"] as const,
  transactionStatsSummary: (
    dateFrom: string,
    dateTo: string,
    accountId?: string,
    search?: string,
    categoryId?: string,
  ) =>
    [
      "transaction-stats",
      "summary",
      dateFrom,
      dateTo,
      accountId,
      search,
      categoryId,
    ] as const,
  transactionStatsMonthly: (
    dateFrom: string,
    dateTo: string,
    accountId?: string,
  ) => ["transaction-stats", "monthly", dateFrom, dateTo, accountId] as const,
  transactionStatsByCategory: (
    dateFrom: string,
    dateTo: string,
    accountId?: string,
  ) => ["transaction-stats", "category", dateFrom, dateTo, accountId] as const,

  categories: ["categories"] as const,
  categorySuggestions: (accountId: string, transactionId: string) =>
    ["categories", "suggestions", accountId, transactionId] as const,

  syncOperations: ["sync-operations"] as const,
  scheduleSettings: ["schedule-settings"] as const,

  bankConnections: ["bank-connections"] as const,
  bankInstitutions: (country: string) =>
    ["bank-institutions", country] as const,
  supportedCountries: ["supported-countries"] as const,

  notificationSettings: ["notification-settings"] as const,
  notificationServices: ["notification-services"] as const,

  backupSettings: ["backup-settings"] as const,
  backups: ["backups"] as const,

  health: ["health"] as const,
};

/**
 * Everything derived from synced bank data. A sync rewrites transactions,
 * balances and the stats computed from them, so all of it has to refetch.
 *
 * Call sites used to keep their own copies of this list, which had already
 * drifted — one invalidated "banks", another "balances", neither both.
 */
export function invalidateSyncedData(queryClient: QueryClient): void {
  const roots = [
    queryKeys.accounts,
    queryKeys.balances,
    queryKeys.transactions,
    queryKeys.transactionStats,
    queryKeys.syncOperations,
    queryKeys.bankConnections,
  ];
  for (const queryKey of roots) {
    queryClient.invalidateQueries({ queryKey });
  }
}

/**
 * Assigning or clearing a category changes the transaction rows and every
 * statistic grouped by category, but leaves balances and accounts alone.
 */
export function invalidateCategorizedData(queryClient: QueryClient): void {
  const roots = [
    queryKeys.transactions,
    queryKeys.transactionStats,
    queryKeys.categories,
  ];
  for (const queryKey of roots) {
    queryClient.invalidateQueries({ queryKey });
  }
}
