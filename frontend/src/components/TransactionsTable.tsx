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
import type { Account, Transaction, ApiResponse, Balance } from "../types/api";

export default function TransactionsTable() {
  // Filter state consolidated into a single object
  const [filterState, setFilterState] = useState<FilterState>({
    searchTerm: "",
    selectedAccount: "",
    startDate: "",
    endDate: "",
    minAmount: "",
    maxAmount: "",
  });

  const [showRawModal, setShowRawModal] = useState(false);
  const [selectedTransaction, setSelectedTransaction] =
    useState<Transaction | null>(null);
  const [showRunningBalance, setShowRunningBalance] = useState(true);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(50);

  // Debounced search state
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState(filterState.searchTerm);

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
      minAmount: "",
      maxAmount: "",
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

  const { data: balances } = useQuery<Balance[]>({
    queryKey: ["balances"],
    queryFn: apiClient.getBalances,
    enabled: showRunningBalance,
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
      filterState.minAmount,
      filterState.maxAmount,
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
        minAmount: filterState.minAmount ? parseFloat(filterState.minAmount) : undefined,
        maxAmount: filterState.maxAmount ? parseFloat(filterState.maxAmount) : undefined,
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
  }, [filterState.selectedAccount, filterState.startDate, filterState.endDate, filterState.minAmount, filterState.maxAmount]);

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
    filterState.endDate ||
    filterState.minAmount ||
    filterState.maxAmount;

  // Calculate running balances
  const calculateRunningBalances = (transactions: Transaction[]) => {
    if (!balances || !showRunningBalance) return {};

    const runningBalances: { [key: string]: number } = {};
    const accountBalanceMap = new Map<string, number>();

    // Create a map of account current balances
    balances.forEach(balance => {
      if (balance.balance_type === 'expected') {
        accountBalanceMap.set(balance.account_id, balance.balance_amount);
      }
    });

    // Group transactions by account
    const transactionsByAccount = new Map<string, Transaction[]>();
    transactions.forEach(txn => {
      if (!transactionsByAccount.has(txn.account_id)) {
        transactionsByAccount.set(txn.account_id, []);
      }
      transactionsByAccount.get(txn.account_id)!.push(txn);
    });

    // Calculate running balance for each account
    transactionsByAccount.forEach((accountTransactions, accountId) => {
      const currentBalance = accountBalanceMap.get(accountId) || 0;
      let runningBalance = currentBalance;

      // Sort transactions by date (newest first) to work backwards
      const sortedTransactions = [...accountTransactions].sort((a, b) =>
        new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime()
      );

      // Calculate running balance by working backwards from current balance
      sortedTransactions.forEach((txn) => {
        runningBalances[`${txn.account_id}-${txn.transaction_id}`] = runningBalance;
        runningBalance -= txn.transaction_value;
      });
    });

    return runningBalances;
  };

  const runningBalances = calculateRunningBalances(transactions);

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
              <h4 className="text-sm font-medium text-gray-900 truncate">
                {transaction.description}
              </h4>
              <div className="text-xs text-gray-500 space-y-1">
                {account && (
                  <p className="truncate">
                    {account.name || "Unnamed Account"} •{" "}
                    {account.institution_id}
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
    ...(showRunningBalance ? [{
      id: "running_balance",
      header: "Running Balance",
      cell: ({ row }: { row: { original: Transaction } }) => {
        const transaction = row.original;
        const balanceKey = `${transaction.account_id}-${transaction.transaction_id}`;
        const balance = runningBalances[balanceKey];

        if (balance === undefined) return null;

        return (
          <div className="text-right">
            <p className="text-sm font-medium text-gray-900">
              {formatCurrency(balance, transaction.transaction_currency)}
            </p>
          </div>
        );
      },
    }] : []),
    {
      accessorKey: "transaction_date",
      header: "Date",
      cell: ({ row }) => {
        const transaction = row.original;
        return (
          <div className="text-sm text-gray-900">
            {transaction.transaction_date
              ? formatDate(transaction.transaction_date)
              : "No date"}
            {transaction.booking_date &&
              transaction.booking_date !== transaction.transaction_date && (
                <p className="text-xs text-gray-400">
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
            className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
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
    onGlobalFilterChange: (value: string) => handleFilterChange("searchTerm", value),
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
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center text-center">
          <div>
            <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Failed to load transactions
            </h3>
            <p className="text-gray-600 mb-4">
              Unable to fetch transactions from the Leggen API.
            </p>
            <button
              onClick={() => refetchTransactions()}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* New FilterBar */}
      <FilterBar
        filterState={filterState}
        onFilterChange={handleFilterChange}
        onClearFilters={handleClearFilters}
        accounts={accounts}
        isSearchLoading={isSearchLoading}
        showRunningBalance={showRunningBalance}
        onToggleRunningBalance={() => setShowRunningBalance(!showRunningBalance)}
      />

      {/* Results Summary */}
      <div className="bg-white rounded-lg shadow border">
        <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
          <p className="text-sm text-gray-600">
            Showing {transactions.length} transaction
            {transactions.length !== 1 ? "s" : ""} (
            {pagination ? (
              <>
                {(pagination.page - 1) * pagination.per_page + 1}-
                {Math.min(
                  pagination.page * pagination.per_page,
                  pagination.total,
                )}{" "}
                of {pagination.total}
              </>
            ) : (
              "loading..."
            )}
            )
            {filterState.selectedAccount && accounts && (
              <span className="ml-1">
                for {accounts.find((acc) => acc.id === filterState.selectedAccount)?.name}
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Responsive Table/Cards */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {/* Desktop Table View (hidden on mobile) */}
        <div className="hidden md:block">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <th
                        key={header.id}
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
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
                                    ? "text-blue-600"
                                    : "text-gray-400"
                                }`}
                              />
                              <ChevronDown
                                className={`h-3 w-3 -mt-1 ${
                                  header.column.getIsSorted() === "desc"
                                    ? "text-blue-600"
                                    : "text-gray-400"
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
              <tbody className="bg-white divide-y divide-gray-200">
                {table.getRowModel().rows.length === 0 ? (
                  <tr>
                    <td
                      colSpan={columns.length}
                      className="px-6 py-12 text-center"
                    >
                      <div className="text-gray-400 mb-4">
                        <TrendingUp className="h-12 w-12 mx-auto" />
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        No transactions found
                      </h3>
                      <p className="text-gray-600">
                        {hasActiveFilters
                          ? "Try adjusting your filters to see more results."
                          : "No transactions are available for the selected criteria."}
                      </p>
                    </td>
                  </tr>
                ) : (
                  table.getRowModel().rows.map((row) => (
                    <tr key={row.id} className="hover:bg-gray-50">
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
        </div>

        {/* Mobile Card View (visible only on mobile) */}
        <div className="md:hidden">
          {table.getRowModel().rows.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <div className="text-gray-400 mb-4">
                <TrendingUp className="h-12 w-12 mx-auto" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No transactions found
              </h3>
              <p className="text-gray-600">
                {hasActiveFilters
                  ? "Try adjusting your filters to see more results."
                  : "No transactions are available for the selected criteria."}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {table.getRowModel().rows.map((row) => {
                const transaction = row.original;
                const account = accounts?.find(
                  (acc) => acc.id === transaction.account_id,
                );
                const isPositive = transaction.transaction_value > 0;

                return (
                  <div
                    key={row.id}
                    className="p-4 hover:bg-gray-50 transition-colors"
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
                            <h4 className="text-sm font-medium text-gray-900 break-words">
                              {transaction.description}
                            </h4>
                            <div className="text-xs text-gray-500 space-y-1 mt-1">
                              {account && (
                                <p className="break-words">
                                  {account.name || "Unnamed Account"} •{" "}
                                  {account.institution_id}
                                </p>
                              )}
                              {(transaction.creditor_name || transaction.debtor_name) && (
                                <p className="break-words">
                                  {isPositive ? "From: " : "To: "}
                                  {transaction.creditor_name || transaction.debtor_name}
                                </p>
                              )}
                              {transaction.reference && (
                                <p className="break-words">Ref: {transaction.reference}</p>
                              )}
                              <p className="text-gray-400">
                                {transaction.transaction_date
                                  ? formatDate(transaction.transaction_date)
                                  : "No date"}
                                {transaction.booking_date &&
                                  transaction.booking_date !== transaction.transaction_date && (
                                    <span className="ml-2">
                                      (Booked: {formatDate(transaction.booking_date)})
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
                        {showRunningBalance && (
                          <p className="text-xs text-gray-500 mb-1">
                            Balance: {formatCurrency(
                              runningBalances[`${transaction.account_id}-${transaction.transaction_id}`] || 0,
                              transaction.transaction_currency,
                            )}
                          </p>
                        )}
                        <button
                          onClick={() => handleViewRaw(transaction)}
                          className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
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
          <div className="bg-white px-4 py-3 flex flex-col sm:flex-row items-center justify-between border-t border-gray-200 space-y-3 sm:space-y-0">
            {/* Mobile pagination controls */}
            <div className="flex justify-between w-full sm:hidden">
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage(1)}
                  disabled={pagination.page === 1}
                  className="relative inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  First
                </button>
                <button
                  onClick={() =>
                    setCurrentPage((prev) => Math.max(1, prev - 1))
                  }
                  disabled={!pagination.has_prev}
                  className="relative inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage((prev) => prev + 1)}
                  disabled={!pagination.has_next}
                  className="relative inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
                <button
                  onClick={() => setCurrentPage(pagination.total_pages)}
                  disabled={pagination.page === pagination.total_pages}
                  className="relative inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Last
                </button>
              </div>
            </div>

            {/* Mobile pagination info */}
            <div className="text-center w-full sm:hidden">
              <p className="text-sm text-gray-700">
                Page <span className="font-medium">{pagination.page}</span> of{" "}
                <span className="font-medium">{pagination.total_pages}</span>
                <br />
                <span className="text-xs text-gray-500">
                  Showing {(pagination.page - 1) * pagination.per_page + 1}-
                  {Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total}
                </span>
              </p>
            </div>

            {/* Desktop pagination */}
            <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
              <div className="flex items-center space-x-2">
                <p className="text-sm text-gray-700">
                  Showing{" "}
                  <span className="font-medium">
                    {(pagination.page - 1) * pagination.per_page + 1}
                  </span>{" "}
                  to{" "}
                  <span className="font-medium">
                    {Math.min(
                      pagination.page * pagination.per_page,
                      pagination.total,
                    )}
                  </span>{" "}
                  of <span className="font-medium">{pagination.total}</span>{" "}
                  results
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <label className="text-sm text-gray-700">
                    Rows per page:
                  </label>
                  <select
                    value={perPage}
                    onChange={(e) => {
                      setPerPage(Number(e.target.value));
                      setCurrentPage(1); // Reset to first page when changing page size
                    }}
                    className="border border-gray-300 rounded px-2 py-1 text-sm"
                  >
                    {[10, 25, 50, 100].map((pageSize) => (
                      <option key={pageSize} value={pageSize}>
                        {pageSize}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setCurrentPage(1)}
                    disabled={pagination.page === 1}
                    className="relative inline-flex items-center px-2 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    First
                  </button>
                  <button
                    onClick={() =>
                      setCurrentPage((prev) => Math.max(1, prev - 1))
                    }
                    disabled={!pagination.has_prev}
                    className="relative inline-flex items-center px-2 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-gray-700">
                    Page <span className="font-medium">{pagination.page}</span>{" "}
                    of{" "}
                    <span className="font-medium">
                      {pagination.total_pages}
                    </span>
                  </span>
                  <button
                    onClick={() => setCurrentPage((prev) => prev + 1)}
                    disabled={!pagination.has_next}
                    className="relative inline-flex items-center px-2 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                  <button
                    onClick={() => setCurrentPage(pagination.total_pages)}
                    disabled={pagination.page === pagination.total_pages}
                    className="relative inline-flex items-center px-2 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Last
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

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
