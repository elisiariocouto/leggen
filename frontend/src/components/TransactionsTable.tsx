import { useState, useEffect, useMemo } from "react";
import { format } from "date-fns";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  AlertCircle,
  ArrowUp,
  ArrowDown,
  ArrowUpDown,
  Loader2,
} from "lucide-react";
import { apiClient } from "../lib/api";
import { formatCurrency, formatDate } from "../lib/utils";
import TransactionSkeleton from "./TransactionSkeleton";
import TransactionDetail from "./TransactionDetail";
import { FilterBar, SortSelect, type FilterState } from "./filters";
import { DataTablePagination } from "./ui/data-table-pagination";
import { Card } from "./ui/card";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Button } from "./ui/button";
import { BlurredValue } from "./ui/blurred-value";
import CategoryBadge from "./CategoryBadge";
import TransactionStatusBadge from "./TransactionStatusBadge";
import type {
  Account,
  Transaction,
  PaginatedResponse,
  TransactionStats,
} from "../types/api";
import { queryKeys } from "../lib/queryKeys";
import { asNonNegativeNumber } from "../lib/searchParams";
import type { SortDirection, TransactionSortField } from "../lib/searchParams";
import type { TransactionSearch } from "../routes/index";

/**
 * Table columns. `sortKey` is the API's sort field; a column without one is
 * not sortable (Category comes from a join and has no backend sort field).
 */
const COLUMNS: Array<{
  id: string;
  label: string;
  sortKey?: TransactionSortField;
  align?: "right";
}> = [
  { id: "description", label: "Description", sortKey: "description" },
  { id: "category", label: "Category" },
  { id: "amount", label: "Amount", sortKey: "amount", align: "right" },
  { id: "date", label: "Date", sortKey: "date" },
];

/**
 * Sort arrow for a column header.
 *
 * `placeholderData` keeps the previous rows on screen while a re-sort is in
 * flight, so without a pending state the table would sit in the old order
 * with nothing to show the click registered.
 */
function SortIndicator({
  isSorted,
  direction,
  isPending,
}: {
  isSorted: boolean;
  direction: SortDirection;
  isPending: boolean;
}) {
  if (isPending) {
    return (
      <Loader2 className="h-3 w-3 animate-spin" aria-label="Sorting" />
    );
  }
  if (!isSorted) {
    return <ArrowUpDown className="h-3 w-3 opacity-40" aria-hidden="true" />;
  }
  return direction === "asc" ? (
    <ArrowUp className="h-3 w-3" aria-hidden="true" />
  ) : (
    <ArrowDown className="h-3 w-3" aria-hidden="true" />
  );
}

/** Up/down arrow on its tinted circle, shared by both layouts. */
function DirectionIcon({ isPositive }: { isPositive: boolean }) {
  return (
    <div
      className={`p-2 rounded-full shrink-0 ${
        isPositive ? "bg-positive-muted" : "bg-negative-muted"
      }`}
    >
      {isPositive ? (
        <TrendingUp className="h-4 w-4 text-positive" />
      ) : (
        <TrendingDown className="h-4 w-4 text-negative" />
      )}
    </div>
  );
}

function Amount({ transaction }: { transaction: Transaction }) {
  const isPositive = transaction.transaction_value > 0;
  return (
    <p
      className={`text-lg font-semibold ${
        isPositive ? "text-positive" : "text-negative"
      }`}
    >
      <BlurredValue>
        {isPositive ? "+" : ""}
        {formatCurrency(
          transaction.transaction_value,
          transaction.transaction_currency,
        )}
      </BlurredValue>
    </p>
  );
}

function TransactionCategory({ transaction }: { transaction: Transaction }) {
  return (
    <CategoryBadge
      accountId={transaction.account_id}
      transactionId={transaction.transaction_id}
      categoryId={transaction.category_id}
      categoryName={transaction.category_name}
      categoryColor={transaction.category_color}
      description={transaction.description}
    />
  );
}

function transactionDate(transaction: Transaction): string {
  return transaction.transaction_date
    ? formatDate(transaction.transaction_date)
    : "No date";
}

function EmptyState({ hasActiveFilters }: { hasActiveFilters: boolean }) {
  return (
    <div className="px-6 py-12 text-center">
      <div className="text-muted-foreground mb-4">
        <TrendingUp className="h-12 w-12 mx-auto" />
      </div>
      <h3 className="text-lg font-medium text-foreground mb-2">
        No transactions found
      </h3>
      <p className="text-muted-foreground">
        {hasActiveFilters
          ? "Try adjusting your filters to see more results."
          : "No transactions are available for the selected criteria."}
      </p>
    </div>
  );
}

export default function TransactionsTable() {
  // Filters and pagination live in the URL, so a filtered view survives a
  // refresh, can be shared, and steps back through history.
  const search = useSearch({ from: "/" });
  const navigate = useNavigate({ from: "/" });

  const filterState: FilterState = useMemo(
    () => ({
      searchTerm: search.q ?? "",
      selectedAccount: search.account ?? "",
      selectedCategory: search.category ?? "",
      selectedStatus: search.status ?? "",
      startDate: search.from ?? "",
      endDate: search.to ?? "",
      minAmount: search.minAmount?.toString() ?? "",
      maxAmount: search.maxAmount?.toString() ?? "",
    }),
    [
      search.q,
      search.account,
      search.category,
      search.status,
      search.from,
      search.to,
      search.minAmount,
      search.maxAmount,
    ],
  );

  // Sort is a view preference rather than a filter: it has no chip, and it
  // survives Clear All. Absent params mean the default ordering.
  const sortBy = search.sort ?? "date";
  const sortOrder = search.dir ?? "desc";

  const currentPage = search.page ?? 1;
  const perPage = search.perPage ?? 50;

  // Transaction detail panel state. The transaction is stored by key and
  // re-derived from the query data below, so category changes made while
  // the panel is open (which invalidate ["transactions"]) refresh it too.
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedKey, setSelectedKey] = useState<{
    accountId: string;
    transactionId: string;
  } | null>(null);
  const [selectedSnapshot, setSelectedSnapshot] = useState<Transaction | null>(
    null,
  );

  // What is being typed, held locally so keystrokes are not throttled by
  // navigation. Stored alongside the URL value it was typed against: when
  // the URL moves on its own (a back step, Clear All), the draft no longer
  // matches and the URL wins, with no effect needed to resync.
  const urlSearch = search.q ?? "";
  const [draft, setDraft] = useState({ value: urlSearch, from: urlSearch });
  const searchInput = draft.from === urlSearch ? draft.value : urlSearch;
  const setSearchInput = (value: string) =>
    setDraft({ value, from: urlSearch });
  const debouncedSearchTerm = urlSearch;

  // Changing a filter always returns to page 1 — the old page number rarely
  // exists in the new result set. Done in the same navigation as the filter
  // itself, so only one request goes out.
  const handleFilterChange = (key: keyof FilterState, value: string) => {
    const paramFor: Record<keyof FilterState, keyof typeof search> = {
      searchTerm: "q",
      selectedAccount: "account",
      selectedCategory: "category",
      selectedStatus: "status",
      startDate: "from",
      endDate: "to",
      minAmount: "minAmount",
      maxAmount: "maxAmount",
    };
    if (key === "searchTerm") setSearchInput(value);
    // The amount bounds are numbers in the URL schema; everything else is a
    // string. An unparseable or negative entry drops the bound rather than
    // writing a value validateSearch would reject on the next read.
    const isAmount = key === "minAmount" || key === "maxAmount";
    const nextValue = isAmount
      ? asNonNegativeNumber(value)
      : value || undefined;
    navigate({
      search: (prev: TransactionSearch) => ({
        ...prev,
        [paramFor[key]]: nextValue,
        page: undefined,
      }),
      replace: key === "searchTerm" || isAmount,
    });
  };

  const handleClearFilters = () => {
    setSearchInput("");
    // Sort and page size are view preferences, not filters, so they survive.
    navigate({
      search: (prev: TransactionSearch) => ({
        perPage: prev.perPage,
        sort: prev.sort,
        dir: prev.dir,
      }),
    });
  };

  const handleSortChange = (
    nextSort: TransactionSortField,
    nextDir: SortDirection,
  ) => {
    navigate({
      search: (prev: TransactionSearch) => ({
        ...prev,
        // Omit the defaults so a plain "/" stays the canonical URL.
        sort: nextSort === "date" ? undefined : nextSort,
        dir: nextDir === "desc" ? undefined : nextDir,
        page: undefined,
      }),
    });
  };

  // Clicking the active column flips direction; a new column starts
  // descending, which is the useful default for both dates and amounts.
  const handleSortColumn = (column: TransactionSortField) => {
    if (column === sortBy) {
      handleSortChange(column, sortOrder === "asc" ? "desc" : "asc");
    } else {
      handleSortChange(column, "desc");
    }
  };

  const setCurrentPage = (page: number) => {
    navigate({ search: (prev: TransactionSearch) => ({ ...prev, page: page > 1 ? page : undefined }) });
  };

  const setPerPage = (size: number) => {
    navigate({
      search: (prev: TransactionSearch) => ({
        ...prev,
        perPage: size === 50 ? undefined : size,
        page: undefined,
      }),
    });
  };

  // Push the typed term into the URL once typing settles.
  useEffect(() => {
    if (searchInput === (search.q ?? "")) return;
    const timer = setTimeout(() => {
      handleFilterChange("searchTerm", searchInput);
    }, 300);
    return () => clearTimeout(timer);
    // handleFilterChange is stable enough for this effect's purpose; it only
    // closes over navigate, which TanStack keeps referentially stable.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput, search.q]);

  const { data: accounts } = useQuery<Account[]>({
    queryKey: queryKeys.accounts,
    queryFn: apiClient.getAccounts,
  });

  const {
    data: transactionsResponse,
    isLoading: transactionsLoading,
    isFetching,
    error: transactionsError,
    refetch: refetchTransactions,
  } = useQuery<PaginatedResponse<Transaction>>({
    queryKey: queryKeys.transactionList({
      accountId: filterState.selectedAccount,
      categoryId: filterState.selectedCategory,
      status: filterState.selectedStatus,
      startDate: filterState.startDate,
      endDate: filterState.endDate,
      page: currentPage,
      perPage,
      search: debouncedSearchTerm,
      minAmount: search.minAmount,
      maxAmount: search.maxAmount,
      sortBy,
      sortOrder,
    }),
    queryFn: () =>
      apiClient.getTransactions({
        accountId: filterState.selectedAccount || undefined,
        startDate: filterState.startDate || undefined,
        endDate: filterState.endDate || undefined,
        page: currentPage,
        perPage: perPage,
        search: debouncedSearchTerm || undefined,
        summaryOnly: false,
        categoryId: filterState.selectedCategory || undefined,
        status: filterState.selectedStatus || undefined,
        minMagnitude: search.minAmount,
        maxMagnitude: search.maxAmount,
        sortBy,
        sortOrder,
      }),
    placeholderData: (previousData) => previousData,
  });

  const transactions = useMemo(
    () => transactionsResponse?.data || [],
    [transactionsResponse],
  );

  // One pass instead of a linear find per row per render.
  const accountsById = useMemo(
    () => new Map((accounts ?? []).map((account) => [account.id, account])),
    [accounts],
  );

  const selectedFromQuery = useMemo(
    () =>
      transactions.find(
        (t) =>
          t.account_id === selectedKey?.accountId &&
          t.transaction_id === selectedKey?.transactionId,
      ) ?? null,
    [transactions, selectedKey],
  );
  // Prefer the live row so edits made while the panel is open show up, and
  // fall back to the snapshot taken when it was opened — the row leaves the
  // page if a category filter is active and it was just recategorized, and
  // it is also gone during the closing animation.
  const selectedTransaction = selectedFromQuery ?? selectedSnapshot;

  const openDetail = (transaction: Transaction) => {
    setSelectedKey({
      accountId: transaction.account_id,
      transactionId: transaction.transaction_id,
    });
    setSelectedSnapshot(transaction);
    setDetailOpen(true);
  };
  const pagination = useMemo(
    () =>
      transactionsResponse
        ? {
            page: transactionsResponse.page,
            total_pages: transactionsResponse.total_pages,
            per_page: transactionsResponse.per_page,
            total: transactionsResponse.total,
            has_next: transactionsResponse.has_next,
            has_prev: transactionsResponse.has_prev,
          }
        : undefined,
    [transactionsResponse],
  );

  // Stats cover every transaction matching the filters, not just this page.
  // The date bounds are derived here rather than inside queryFn so they are
  // part of the cache key — otherwise the entry computed before midnight
  // would keep serving a stale "today".
  const statsRange = useMemo(() => {
    const today = format(new Date(), "yyyy-MM-dd");
    return {
      from: filterState.startDate || "2000-01-01",
      to: filterState.endDate || today,
    };
  }, [filterState.startDate, filterState.endDate]);

  const { data: statsData } = useQuery<TransactionStats>({
    queryKey: [
      ...queryKeys.transactionStatsSummary(
        statsRange.from,
        statsRange.to,
        filterState.selectedAccount,
        debouncedSearchTerm,
        filterState.selectedCategory,
      ),
      search.minAmount,
      search.maxAmount,
    ],
    queryFn: () =>
      apiClient.getTransactionStats(
        statsRange.from,
        statsRange.to,
        filterState.selectedAccount || undefined,
        debouncedSearchTerm || undefined,
        undefined,
        undefined,
        filterState.selectedCategory || undefined,
        {
          minMagnitude: search.minAmount,
          maxMagnitude: search.maxAmount,
        },
      ),
    placeholderData: (previousData) => previousData,
  });

  // Stats totals are per dominant currency (reported by the backend);
  // fall back to the current page's currency
  const displayCurrency =
    statsData?.currency ??
    (transactions.length > 0 ? transactions[0].transaction_currency : "EUR");

  // Check if search is currently debouncing
  // True while the typed term has not yet reached the URL and the query.
  const isSearchLoading = searchInput !== debouncedSearchTerm;

  // The bar shows what is being typed; everything else reflects the URL.
  const displayedFilterState: FilterState = useMemo(
    () => ({ ...filterState, searchTerm: searchInput }),
    [filterState, searchInput],
  );

  // A link can point past the end of the result set — go back to page 1
  // rather than showing an empty table. Filter changes reset the page in
  // handleFilterChange, so this only catches the deep-link case.
  useEffect(() => {
    if (!pagination || currentPage === 1) return;
    if (currentPage > pagination.total_pages) {
      navigate({ search: (prev: TransactionSearch) => ({ ...prev, page: undefined }) });
    }
  }, [pagination, currentPage, navigate]);

  const hasActiveFilters =
    filterState.searchTerm ||
    filterState.selectedAccount ||
    filterState.selectedCategory ||
    filterState.selectedStatus ||
    filterState.startDate ||
    filterState.endDate;

  const isEmpty = transactions.length === 0;

  if (transactionsLoading) {
    // The filter bar is driven by its own queries, so it stays interactive
    // while the transaction page loads underneath it.
    return (
      <div className="max-w-full">
        <Card>
          <FilterBar
            filterState={displayedFilterState}
            onFilterChange={handleFilterChange}
            onClearFilters={handleClearFilters}
            accounts={accounts}
            isSearchLoading={isSearchLoading}
            currency={displayCurrency}
          />
          <div className="hidden md:block">
            <TransactionSkeleton rows={10} view="table" />
          </div>
          <div className="md:hidden">
            <TransactionSkeleton rows={10} view="mobile" />
          </div>
        </Card>
      </div>
    );
  }

  if (transactionsError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Failed to load transactions</AlertTitle>
        <AlertDescription className="space-y-3">
          <p>Unable to fetch transactions from the Leggen API.</p>
          <Button
            onClick={() => refetchTransactions()}
            variant="outline"
            size="sm"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="max-w-full">
      <Card>
        {/* Header: Filters */}
        <FilterBar
          filterState={displayedFilterState}
          onFilterChange={handleFilterChange}
          onClearFilters={handleClearFilters}
          accounts={accounts}
          isSearchLoading={isSearchLoading}
          currency={displayCurrency}
        />

        {/* Stats Bar */}
        {transactions.length > 0 && statsData && (
          <div className="px-6 py-2 border-t bg-muted/30">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
              <span className="text-muted-foreground">
                {transactions.length} of {(pagination?.total || 0).toLocaleString()}
              </span>
              <span className="text-muted-foreground hidden sm:inline">·</span>
              <BlurredValue>
                <span className="text-positive">
                  +{formatCurrency(statsData.total_income, displayCurrency)} income
                </span>
              </BlurredValue>
              <span className="text-muted-foreground hidden sm:inline">·</span>
              <BlurredValue>
                <span className="text-negative">
                  -{formatCurrency(statsData.total_expenses, displayCurrency)} expenses
                </span>
              </BlurredValue>
              <span className="text-muted-foreground hidden sm:inline">·</span>
              <BlurredValue>
                <span className={statsData.net_change >= 0 ? "text-positive" : "text-negative"}>
                  Net {statsData.net_change >= 0 ? "+" : ""}
                  {formatCurrency(statsData.net_change, displayCurrency)}
                </span>
              </BlurredValue>
            </div>
          </div>
        )}

        {/* One empty state for both layouts, rather than the same copy
            repeated inside each breakpoint branch. */}
        {isEmpty && <EmptyState hasActiveFilters={!!hasActiveFilters} />}

        {/* Desktop Table View (hidden on mobile) */}
        <div className={isEmpty ? "hidden" : "hidden md:block"}>
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-muted/50">
              <tr>
                {COLUMNS.map((column) => {
                  const isSorted = column.sortKey === sortBy;
                  const alignment =
                    column.align === "right" ? "text-right" : "text-left";
                  return (
                    <th
                      key={column.id}
                      scope="col"
                      // Announces the sort state to screen readers; the
                      // arrow alone is only available visually.
                      aria-sort={
                        isSorted
                          ? sortOrder === "asc"
                            ? "ascending"
                            : "descending"
                          : undefined
                      }
                      className={`px-6 py-3 ${alignment} text-xs font-medium text-muted-foreground uppercase tracking-wider`}
                    >
                      {column.sortKey ? (
                        <button
                          type="button"
                          onClick={() => handleSortColumn(column.sortKey!)}
                          className={`inline-flex items-center gap-1 uppercase tracking-wider hover:text-foreground focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring rounded-sm ${
                            column.align === "right" ? "flex-row-reverse" : ""
                          } ${isSorted ? "text-foreground" : ""}`}
                        >
                          {column.label}
                          <SortIndicator
                            isSorted={isSorted}
                            direction={sortOrder}
                            isPending={isSorted && isFetching}
                          />
                        </button>
                      ) : (
                        column.label
                      )}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {transactions.map((transaction) => {
                const account = accountsById.get(transaction.account_id);
                return (
                  <tr
                    key={`${transaction.account_id}-${transaction.transaction_id}`}
                    className="hover:bg-muted/50 cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
                    // The row is the control that opens the detail panel, so
                    // it has to be reachable and activatable from the keyboard.
                    tabIndex={0}
                    aria-label={`Transaction ${transaction.description}, ${formatCurrency(
                      transaction.transaction_value,
                      transaction.transaction_currency,
                    )}. Open details`}
                    onClick={() => openDetail(transaction)}
                    onKeyDown={(e) => {
                      if (e.target !== e.currentTarget) return;
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        openDetail(transaction);
                      }
                    }}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-start space-x-3">
                        <DirectionIcon
                          isPositive={transaction.transaction_value > 0}
                        />
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-foreground truncate">
                            {transaction.description}
                          </h4>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            {account && (
                              <span className="truncate">
                                {account.display_name || "Unnamed Account"}
                              </span>
                            )}
                            {/* Booked is the norm and says nothing useful, so
                                only pending rows are marked — a chip on the
                                row rather than a column of mostly-blank cells. */}
                            <TransactionStatusBadge
                              status={transaction.transaction_status}
                              pendingOnly
                              className="shrink-0"
                            />
                          </div>
                        </div>
                      </div>
                    </td>
                    <td
                      className="px-6 py-4 whitespace-nowrap"
                      // Keep category popover interactions from opening the
                      // detail panel (Radix portals bubble in the React tree)
                      onClick={(e) => e.stopPropagation()}
                    >
                      <TransactionCategory transaction={transaction} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-right">
                        <Amount transaction={transaction} />
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-foreground">
                        {transactionDate(transaction)}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* The card layout has no header row to click, so sorting gets its
            own control here. */}
        <div
          className={
            isEmpty
              ? "hidden"
              : "md:hidden flex items-center justify-between gap-3 border-t px-4 py-3"
          }
        >
          <span className="text-xs text-muted-foreground uppercase tracking-wider">
            Sort
          </span>
          <SortSelect
            sort={sortBy}
            dir={sortOrder}
            onSortChange={handleSortChange}
            className="w-[190px]"
          />
        </div>

        {/* Mobile Card View (visible only on mobile) */}
        <div
          className={
            isEmpty ? "hidden" : "md:hidden divide-y divide-border"
          }
        >
          {transactions.map((transaction) => {
                const account = accountsById.get(transaction.account_id);
                const isPositive = transaction.transaction_value > 0;

                return (
                  <div
                    key={`${transaction.account_id}-${transaction.transaction_id}`}
                    className="p-4 hover:bg-muted/50 transition-colors cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
                    role="button"
                    tabIndex={0}
                    aria-label={`Transaction ${transaction.description}, ${formatCurrency(
                      transaction.transaction_value,
                      transaction.transaction_currency,
                    )}. Open details`}
                    onClick={() => openDetail(transaction)}
                    onKeyDown={(e) => {
                      if (e.target !== e.currentTarget) return;
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        openDetail(transaction);
                      }
                    }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start space-x-3">
                          <div
                            className={`p-2 rounded-full shrink-0 ${
                              isPositive
                                ? "bg-positive-muted"
                                : "bg-negative-muted"
                            }`}
                          >
                            {isPositive ? (
                              <TrendingUp className="h-4 w-4 text-positive" />
                            ) : (
                              <TrendingDown className="h-4 w-4 text-negative" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-medium text-foreground wrap-break-word">
                              {transaction.description}
                            </h4>
                            <div className="text-xs text-muted-foreground space-y-1 mt-1">
                              {account && (
                                <p className="wrap-break-word">
                                  {account.display_name || "Unnamed Account"}
                                </p>
                              )}
                              <div className="flex items-center gap-2">
                                <span className="text-muted-foreground">
                                  {transaction.transaction_date
                                    ? formatDate(transaction.transaction_date)
                                    : "No date"}
                                </span>
                                <TransactionStatusBadge
                                  status={transaction.transaction_status}
                                  pendingOnly
                                  className="shrink-0"
                                />
                              </div>
                              <div
                                className="mt-1"
                                // Keep category popover interactions from
                                // opening the detail panel
                                onClick={(e) => e.stopPropagation()}
                              >
                                <CategoryBadge
                                  accountId={transaction.account_id}
                                  transactionId={transaction.transaction_id}
                                  categoryId={transaction.category_id}
                                  categoryName={transaction.category_name}
                                  categoryColor={transaction.category_color}
                                  description={transaction.description}
                                />
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="text-right ml-3 shrink-0">
                        <p
                          className={`text-lg font-semibold ${
                            isPositive
                              ? "text-positive"
                              : "text-negative"
                          }`}
                        >
                          <BlurredValue>
                            {isPositive ? "+" : ""}
                            {formatCurrency(
                              transaction.transaction_value,
                              transaction.transaction_currency,
                            )}
                          </BlurredValue>
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
        </div>

        {/* Pagination */}
        {pagination && (
          <DataTablePagination
            currentPage={pagination.page}
            totalPages={pagination.total_pages}
            pageSize={pagination.per_page}
            total={pagination.total}
            hasNext={pagination.has_next}
            hasPrev={pagination.has_prev}
            onPageChange={setCurrentPage}
            onPageSizeChange={setPerPage}
          />
        )}
      </Card>

      <TransactionDetail
        transaction={selectedTransaction}
        open={detailOpen && !!selectedTransaction}
        onOpenChange={setDetailOpen}
        accounts={accounts}
      />
    </div>
  );
}
