import { useState, useEffect, useMemo, useRef } from "react";
import { format } from "date-fns";
import { useQuery } from "@tanstack/react-query";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
} from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { apiClient } from "../lib/api";
import { formatCurrency, formatDate } from "../lib/utils";
import TransactionSkeleton from "./TransactionSkeleton";
import FiltersSkeleton from "./FiltersSkeleton";
import TransactionDetail from "./TransactionDetail";
import { FilterBar, type FilterState } from "./filters";
import { DataTablePagination } from "./ui/data-table-pagination";
import { Card } from "./ui/card";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Button } from "./ui/button";
import { BlurredValue } from "./ui/blurred-value";
import CategoryBadge from "./CategoryBadge";
import type {
  Account,
  Transaction,
  PaginatedResponse,
  TransactionStats,
} from "../types/api";

export default function TransactionsTable() {
  // Filter state consolidated into a single object
  const [filterState, setFilterState] = useState<FilterState>({
    searchTerm: "",
    selectedAccount: "",
    selectedCategory: "",
    startDate: "",
    endDate: "",
  });

  // Transaction detail panel state. The transaction is stored by key and
  // re-derived from the query data below, so category changes made while
  // the panel is open (which invalidate ["transactions"]) refresh it too.
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedKey, setSelectedKey] = useState<{
    accountId: string;
    transactionId: string;
  } | null>(null);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(50);

  // Debounced search state
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState(
    filterState.searchTerm,
  );

  // Helper function to update filter state
  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilterState((prev) => ({ ...prev, [key]: value }));
  };

  // Helper function to clear all filters
  const handleClearFilters = () => {
    setFilterState({
      searchTerm: "",
      selectedAccount: "",
      selectedCategory: "",
      startDate: "",
      endDate: "",
    });
    setCurrentPage(1);
  };

  // Debounce search term to prevent excessive API calls
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(filterState.searchTerm);
    }, 300); // 300ms delay

    return () => clearTimeout(timer);
  }, [filterState.searchTerm]);

  // Reset pagination when debounced search term changes
  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedSearchTerm]);

  const { data: accounts } = useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: apiClient.getAccounts,
  });

  const {
    data: transactionsResponse,
    isLoading: transactionsLoading,
    error: transactionsError,
    refetch: refetchTransactions,
  } = useQuery<PaginatedResponse<Transaction>>({
    queryKey: [
      "transactions",
      filterState.selectedAccount,
      filterState.selectedCategory,
      filterState.startDate,
      filterState.endDate,
      currentPage,
      perPage,
      debouncedSearchTerm,
    ],
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
      }),
    placeholderData: (previousData) => previousData,
  });

  const transactions = useMemo(
    () => transactionsResponse?.data || [],
    [transactionsResponse],
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
  // Snapshot keeps the panel populated if the row leaves the current page
  // (e.g. a category filter is active and the transaction was just
  // recategorized) or during the close animation.
  const lastSelectedRef = useRef<Transaction | null>(null);
  if (selectedFromQuery) lastSelectedRef.current = selectedFromQuery;
  const selectedTransaction = selectedFromQuery ?? lastSelectedRef.current;

  const openDetail = (transaction: Transaction) => {
    setSelectedKey({
      accountId: transaction.account_id,
      transactionId: transaction.transaction_id,
    });
    lastSelectedRef.current = transaction;
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

  // Fetch stats from API (covers all filtered transactions, not just current page)
  const { data: statsData } = useQuery<TransactionStats>({
    queryKey: [
      "transactionStats",
      filterState.selectedAccount,
      filterState.selectedCategory,
      filterState.startDate,
      filterState.endDate,
      debouncedSearchTerm,
    ],
    queryFn: () => {
      const hasDateFilter =
        Boolean(filterState.startDate) || Boolean(filterState.endDate);
      const startDateParam = hasDateFilter
        ? filterState.startDate || "2000-01-01"
        : undefined;
      const today = format(new Date(), "yyyy-MM-dd");
      const endDateParam = hasDateFilter
        ? filterState.endDate || today
        : undefined;

      return apiClient.getTransactionStats(
        startDateParam ?? "2000-01-01",
        endDateParam ?? today,
        filterState.selectedAccount || undefined,
        debouncedSearchTerm || undefined,
        undefined,
        undefined,
        filterState.selectedCategory || undefined,
      );
    },
    placeholderData: (previousData) => previousData,
  });

  // Stats totals are per dominant currency (reported by the backend);
  // fall back to the current page's currency
  const displayCurrency =
    statsData?.currency ??
    (transactions.length > 0 ? transactions[0].transaction_currency : "EUR");

  // Check if search is currently debouncing
  const isSearchLoading = filterState.searchTerm !== debouncedSearchTerm;

  // Reset pagination when total becomes 0 (no results)
  useEffect(() => {
    if (pagination && pagination.total === 0 && currentPage > 1) {
      setCurrentPage(1);
    }
  }, [pagination, currentPage]);

  // Reset pagination when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [filterState.selectedAccount, filterState.selectedCategory, filterState.startDate, filterState.endDate]);

  const hasActiveFilters =
    filterState.searchTerm ||
    filterState.selectedAccount ||
    filterState.selectedCategory ||
    filterState.startDate ||
    filterState.endDate;

  // Define columns
  const columns: ColumnDef<Transaction>[] = [
    {
      accessorKey: "description",
      header: "Description",
      cell: ({ row }) => {
        const transaction = row.original;
        const account = accounts?.find(
          (acc) => acc.id === transaction.account_id,
        );
        const isPositive = transaction.transaction_value > 0;

        return (
          <div className="flex items-start space-x-3">
            <div
              className={`p-2 rounded-full ${
                isPositive
                  ? "bg-green-100 dark:bg-green-900/20"
                  : "bg-red-100 dark:bg-red-900/20"
              }`}
            >
              {isPositive ? (
                <TrendingUp className="h-4 w-4 text-green-600 dark:text-green-400" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600 dark:text-red-400" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-medium text-foreground truncate">
                {transaction.description}
              </h4>
              <div className="text-xs text-muted-foreground space-y-1">
                {account && (
                  <p className="truncate">
                    {account.display_name || "Unnamed Account"}
                  </p>
                )}
              </div>
            </div>
          </div>
        );
      },
    },
    {
      id: "category",
      header: "Category",
      cell: ({ row }) => {
        const transaction = row.original;
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
      },
    },
    {
      accessorKey: "transaction_value",
      header: "Amount",
      cell: ({ row }) => {
        const transaction = row.original;
        const isPositive = transaction.transaction_value > 0;
        return (
          <div className="text-right">
            <p
              className={`text-lg font-semibold ${
                isPositive
                  ? "text-green-600 dark:text-green-400"
                  : "text-red-600 dark:text-red-400"
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
        );
      },
    },
    {
      accessorKey: "transaction_date",
      header: "Date",
      cell: ({ row }) => {
        const transaction = row.original;
        return (
          <div className="text-sm text-foreground">
            {transaction.transaction_date
              ? formatDate(transaction.transaction_date)
              : "No date"}
          </div>
        );
      },
    },
  ];

  // Filtering, sorting, and pagination all happen server-side — the table
  // only renders the current page as-is.
  const table = useReactTable({
    data: transactions,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (transactionsLoading) {
    return (
      <div className="space-y-6">
        <FiltersSkeleton />
        <TransactionSkeleton rows={10} view="table" />
        <div className="md:hidden">
          <TransactionSkeleton rows={10} view="mobile" />
        </div>
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
          filterState={filterState}
          onFilterChange={handleFilterChange}
          onClearFilters={handleClearFilters}
          accounts={accounts}
          isSearchLoading={isSearchLoading}
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
                <span className="text-green-600 dark:text-green-400">
                  +{formatCurrency(statsData.total_income, displayCurrency)} income
                </span>
              </BlurredValue>
              <span className="text-muted-foreground hidden sm:inline">·</span>
              <BlurredValue>
                <span className="text-red-600 dark:text-red-400">
                  -{formatCurrency(statsData.total_expenses, displayCurrency)} expenses
                </span>
              </BlurredValue>
              <span className="text-muted-foreground hidden sm:inline">·</span>
              <BlurredValue>
                <span className={statsData.net_change >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}>
                  Net {statsData.net_change >= 0 ? "+" : ""}
                  {formatCurrency(statsData.net_change, displayCurrency)}
                </span>
              </BlurredValue>
            </div>
          </div>
        )}

        {/* Desktop Table View (hidden on mobile) */}
        <div className="hidden md:block">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-muted/50">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider"
                    >
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {table.getRowModel().rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="px-6 py-12 text-center"
                  >
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
                  </td>
                </tr>
              ) : (
                table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    className="hover:bg-muted/50 cursor-pointer"
                    onClick={() => openDetail(row.original)}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td
                        key={cell.id}
                        className="px-6 py-4 whitespace-nowrap"
                        // Keep category popover interactions from opening the
                        // detail panel (Radix portals bubble in the React tree)
                        onClick={
                          cell.column.id === "category"
                            ? (e) => e.stopPropagation()
                            : undefined
                        }
                      >
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile Card View (visible only on mobile) */}
        <div className="md:hidden">
          {table.getRowModel().rows.length === 0 ? (
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
          ) : (
            <div className="divide-y divide-border">
              {table.getRowModel().rows.map((row) => {
                const transaction = row.original;
                const account = accounts?.find(
                  (acc) => acc.id === transaction.account_id,
                );
                const isPositive = transaction.transaction_value > 0;

                return (
                  <div
                    key={row.id}
                    className="p-4 hover:bg-muted/50 transition-colors cursor-pointer"
                    onClick={() => openDetail(transaction)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start space-x-3">
                          <div
                            className={`p-2 rounded-full shrink-0 ${
                              isPositive
                                ? "bg-green-100 dark:bg-green-900/20"
                                : "bg-red-100 dark:bg-red-900/20"
                            }`}
                          >
                            {isPositive ? (
                              <TrendingUp className="h-4 w-4 text-green-600 dark:text-green-400" />
                            ) : (
                              <TrendingDown className="h-4 w-4 text-red-600 dark:text-red-400" />
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
                              <p className="text-muted-foreground">
                                {transaction.transaction_date
                                  ? formatDate(transaction.transaction_date)
                                  : "No date"}
                              </p>
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
                              ? "text-green-600 dark:text-green-400"
                              : "text-red-600 dark:text-red-400"
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
          )}
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
