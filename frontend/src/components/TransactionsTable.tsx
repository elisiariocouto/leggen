import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
} from "@tanstack/react-table";
import type {
  ColumnDef,
  SortingState,
  ColumnFiltersState,
} from "@tanstack/react-table";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  AlertCircle,
  Eye,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import { apiClient } from "../lib/api";
import { formatCurrency, formatDate } from "../lib/utils";
import TransactionSkeleton from "./TransactionSkeleton";
import FiltersSkeleton from "./FiltersSkeleton";
import RawTransactionModal from "./RawTransactionModal";
import { FilterBar, type FilterState } from "./filters";
import { DataTablePagination } from "./ui/data-table-pagination";
import { Card } from "./ui/card";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Button } from "./ui/button";
import type { Account, Transaction, ApiResponse } from "../types/api";

export default function TransactionsTable() {
  // Filter state consolidated into a single object
  const [filterState, setFilterState] = useState<FilterState>({
    searchTerm: "",
    selectedAccount: "",
    startDate: "",
    endDate: "",
  });

  const [showRawModal, setShowRawModal] = useState(false);
  const [selectedTransaction, setSelectedTransaction] =
    useState<Transaction | null>(null);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(50);

  // Debounced search state
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState(
    filterState.searchTerm,
  );

  // Table state (remove pagination from table)
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);

  // Helper function to update filter state
  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilterState((prev) => ({ ...prev, [key]: value }));
  };

  // Helper function to clear all filters
  const handleClearFilters = () => {
    setFilterState({
      searchTerm: "",
      selectedAccount: "",
      startDate: "",
      endDate: "",
    });
    setColumnFilters([]);
    setCurrentPage(1);
  };

  // Debounce search term to prevent excessive API calls
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(filterState.searchTerm);
    }, 300); // 300ms delay

    return () => clearTimeout(timer);
  }, [filterState.searchTerm]);

  // Reset pagination when search term changes
  useEffect(() => {
    if (debouncedSearchTerm !== filterState.searchTerm) {
      setCurrentPage(1);
    }
  }, [debouncedSearchTerm, filterState.searchTerm]);

  const { data: accounts } = useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: apiClient.getAccounts,
  });

  const {
    data: transactionsResponse,
    isLoading: transactionsLoading,
    error: transactionsError,
    refetch: refetchTransactions,
  } = useQuery<ApiResponse<Transaction[]>>({
    queryKey: [
      "transactions",
      filterState.selectedAccount,
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
      }),
  });

  const transactions = transactionsResponse?.data || [];
  const pagination = transactionsResponse?.pagination;

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
  }, [filterState.selectedAccount, filterState.startDate, filterState.endDate]);

  const handleViewRaw = (transaction: Transaction) => {
    setSelectedTransaction(transaction);
    setShowRawModal(true);
  };

  const handleCloseModal = () => {
    setShowRawModal(false);
    setSelectedTransaction(null);
  };

  const hasActiveFilters =
    filterState.searchTerm ||
    filterState.selectedAccount ||
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
                isPositive ? "bg-green-100" : "bg-red-100"
              }`}
            >
              {isPositive ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600" />
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
                {(transaction.creditor_name || transaction.debtor_name) && (
                  <p className="truncate">
                    {isPositive ? "From: " : "To: "}
                    {transaction.creditor_name || transaction.debtor_name}
                  </p>
                )}
                {transaction.reference && (
                  <p className="truncate">Ref: {transaction.reference}</p>
                )}
              </div>
            </div>
          </div>
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
                isPositive ? "text-green-600" : "text-red-600"
              }`}
            >
              {isPositive ? "+" : ""}
              {formatCurrency(
                transaction.transaction_value,
                transaction.transaction_currency,
              )}
            </p>
          </div>
        );
      },
      sortingFn: "basic",
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
            {transaction.booking_date &&
              transaction.booking_date !== transaction.transaction_date && (
                <p className="text-xs text-muted-foreground">
                  Booked: {formatDate(transaction.booking_date)}
                </p>
              )}
          </div>
        );
      },
      sortingFn: "datetime",
    },
    {
      id: "actions",
      header: "",
      cell: ({ row }) => {
        const transaction = row.original;
        return (
          <button
            onClick={() => handleViewRaw(transaction)}
            className="inline-flex items-center px-2 py-1 text-xs bg-muted text-muted-foreground rounded hover:bg-accent transition-colors"
            title="View raw transaction data"
          >
            <Eye className="h-3 w-3 mr-1" />
            Raw
          </button>
        );
      },
    },
  ];

  const table = useReactTable({
    data: transactions,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    state: {
      sorting,
      columnFilters,
      globalFilter: filterState.searchTerm,
    },
    onGlobalFilterChange: (value: string) =>
      handleFilterChange("searchTerm", value),
    globalFilterFn: (row, _columnId, filterValue) => {
      // Custom global filter that searches multiple fields
      const transaction = row.original;
      const searchLower = filterValue.toLowerCase();

      const description = transaction.description || "";
      const creditorName = transaction.creditor_name || "";
      const debtorName = transaction.debtor_name || "";
      const reference = transaction.reference || "";

      return (
        description.toLowerCase().includes(searchLower) ||
        creditorName.toLowerCase().includes(searchLower) ||
        debtorName.toLowerCase().includes(searchLower) ||
        reference.toLowerCase().includes(searchLower)
      );
    },
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
    <div className="space-y-6 max-w-full">
      {/* New FilterBar */}
      <FilterBar
        filterState={filterState}
        onFilterChange={handleFilterChange}
        onClearFilters={handleClearFilters}
        accounts={accounts}
        isSearchLoading={isSearchLoading}
      />

      {/* Responsive Table/Cards */}
      <Card>
        {/* Desktop Table View (hidden on mobile) */}
        <div className="hidden md:block">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-muted/50">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-muted"
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <div className="flex items-center space-x-1">
                        <span>
                          {header.isPlaceholder
                            ? null
                            : flexRender(
                                header.column.columnDef.header,
                                header.getContext(),
                              )}
                        </span>
                        {header.column.getCanSort() && (
                          <div className="flex flex-col">
                            <ChevronUp
                              className={`h-3 w-3 ${
                                header.column.getIsSorted() === "asc"
                                  ? "text-primary"
                                  : "text-muted-foreground"
                              }`}
                            />
                            <ChevronDown
                              className={`h-3 w-3 -mt-1 ${
                                header.column.getIsSorted() === "desc"
                                  ? "text-primary"
                                  : "text-muted-foreground"
                              }`}
                            />
                          </div>
                        )}
                      </div>
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
                  <tr key={row.id} className="hover:bg-muted/50">
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-6 py-4 whitespace-nowrap">
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
                    className="p-4 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start space-x-3">
                          <div
                            className={`p-2 rounded-full flex-shrink-0 ${
                              isPositive ? "bg-green-100" : "bg-red-100"
                            }`}
                          >
                            {isPositive ? (
                              <TrendingUp className="h-4 w-4 text-green-600" />
                            ) : (
                              <TrendingDown className="h-4 w-4 text-red-600" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-medium text-foreground break-words">
                              {transaction.description}
                            </h4>
                            <div className="text-xs text-muted-foreground space-y-1 mt-1">
                              {account && (
                                <p className="break-words">
                                  {account.display_name || "Unnamed Account"}
                                </p>
                              )}
                              {(transaction.creditor_name ||
                                transaction.debtor_name) && (
                                <p className="break-words">
                                  {isPositive ? "From: " : "To: "}
                                  {transaction.creditor_name ||
                                    transaction.debtor_name}
                                </p>
                              )}
                              {transaction.reference && (
                                <p className="break-words">
                                  Ref: {transaction.reference}
                                </p>
                              )}
                              <p className="text-muted-foreground">
                                {transaction.transaction_date
                                  ? formatDate(transaction.transaction_date)
                                  : "No date"}
                                {transaction.booking_date &&
                                  transaction.booking_date !==
                                    transaction.transaction_date && (
                                    <span className="ml-2">
                                      (Booked:{" "}
                                      {formatDate(transaction.booking_date)})
                                    </span>
                                  )}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="text-right ml-3 flex-shrink-0">
                        <p
                          className={`text-lg font-semibold mb-1 ${
                            isPositive ? "text-green-600" : "text-red-600"
                          }`}
                        >
                          {isPositive ? "+" : ""}
                          {formatCurrency(
                            transaction.transaction_value,
                            transaction.transaction_currency,
                          )}
                        </p>
                        <button
                          onClick={() => handleViewRaw(transaction)}
                          className="inline-flex items-center px-2 py-1 text-xs bg-muted text-muted-foreground rounded hover:bg-accent transition-colors"
                          title="View raw transaction data"
                        >
                          <Eye className="h-3 w-3 mr-1" />
                          Raw
                        </button>
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

      {/* Raw Transaction Modal */}
      <RawTransactionModal
        isOpen={showRawModal}
        onClose={handleCloseModal}
        rawTransaction={selectedTransaction?.raw_transaction}
        transactionId={selectedTransaction?.transaction_id || "unknown"}
      />
    </div>
  );
}
