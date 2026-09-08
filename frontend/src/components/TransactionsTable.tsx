import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Inbox, RefreshCw } from "lucide-react";

import { apiClient } from "@/lib/api";
import { dominantCurrency, formatCurrency } from "@/lib/utils";
import TransactionSkeleton from "./TransactionSkeleton";
import TransactionDetail from "./TransactionDetail";
import { FilterBar, SortSelect } from "./filters";
import { DataTablePagination } from "./ui/data-table-pagination";
import { Card } from "./ui/card";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Button } from "./ui/button";
import { Table, TableBody, TableCell, TableHeader, TableRow } from "./ui/table";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "./ui/empty";
import { BlurredValue } from "./ui/blurred-value";
import { TRANSACTION_COLUMNS } from "./transactions/columns";
import SortableHeader from "./transactions/SortableHeader";
import TransactionRow from "./transactions/TransactionRow";
import TransactionCard from "./transactions/TransactionCard";
import DensityToggle from "./transactions/DensityToggle";
import {
  useTransactionSearch,
  usePageClamp,
} from "@/hooks/useTransactionSearch";
import {
  readStoredDensity,
  writeStoredDensity,
  type Density,
} from "@/lib/density";
import { queryKeys } from "@/lib/queryKeys";
import type { Account, Transaction, PaginatedResponse } from "@/types/api";

/**
 * Zero-result state, rendered as a row inside the table rather than in place
 * of it, so the header — and with it the column names and sort controls —
 * stays put. When a filter returns nothing the next move is usually to adjust
 * that filter, which is hard if the table has vanished.
 */
function EmptyRow({ hasActiveFilters }: { hasActiveFilters: boolean }) {
  return (
    <TableRow className="hover:bg-transparent">
      <TableCell colSpan={TRANSACTION_COLUMNS.length} className="h-64">
        <Empty className="border-0">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <Inbox />
            </EmptyMedia>
            <EmptyTitle>No transactions found</EmptyTitle>
            <EmptyDescription>
              {hasActiveFilters
            ? "Try adjusting your filters to see more results."
            : "No transactions are available for the selected criteria."}
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      </TableCell>
    </TableRow>
  );
}

export default function TransactionsTable() {
  // Filters, sort and pagination all live in the URL — see the hook.
  const {
    search,
    filterState,
    displayedFilterState,
    hasActiveFilters,
    isSearchLoading,
    debouncedSearchTerm,
    sortBy,
    sortOrder,
    currentPage,
    perPage,
    handleFilterChange,
    handleClearFilters,
    handleSortChange,
    handleSortColumn,
    setCurrentPage,
    setPerPage,
  } = useTransactionSearch();

  // Row height is a per-device display preference, so unlike the view state
  // above it is not in the URL.
  const [density, setDensity] = useState<Density>(readStoredDensity);
  const changeDensity = (next: Density) => {
    setDensity(next);
    writeStoredDensity(next);
  };

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

  usePageClamp(currentPage, pagination?.total_pages);

  // Labels the filter bar's amount inputs. Taken from the rows on screen
  // rather than a stats endpoint: it only has to name the currency the user
  // is looking at, and the most common one across the page is that.
  const displayCurrency = useMemo(
    () => dominantCurrency(transactions.map((t) => t.transaction_currency)),
    [transactions],
  );

  // Net movement across the rows on screen. Deliberately this page only, and
  // deliberately understated: the page is a browse-and-search tool, and
  // period-scoped income/expense analysis belongs on Analytics, where it can
  // carry a time axis. An unbounded all-time total here would also double
  // count transfers between the user's own accounts.
  const pageNet = useMemo(
    () => transactions.reduce((sum, t) => sum + t.transaction_value, 0),
    [transactions],
  );

  const filterBar = (
    <FilterBar
      filterState={displayedFilterState}
      onFilterChange={handleFilterChange}
      onClearFilters={handleClearFilters}
      accounts={accounts}
      isSearchLoading={isSearchLoading}
      currency={displayCurrency}
    />
  );

  if (transactionsLoading) {
    // The filter bar is driven by its own queries, so it stays interactive
    // while the transaction page loads underneath it.
    return (
      <div className="max-w-full">
        <Card>
          {filterBar}
          <div className="hidden md:block">
            <TransactionSkeleton rows={10} view="table" density={density} />
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
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  const isEmpty = transactions.length === 0;

  return (
    <div className="max-w-full">
      {/* `overflow-x-clip` keeps the corner clipping that `Card`'s
          `overflow-hidden` provides, while leaving the vertical axis
          unclipped so the table's sticky header can pin to the viewport — a
          clipping ancestor on that axis would stop it dead. */}
      <Card className="overflow-x-clip overflow-y-visible">
        {filterBar}

        {/* Desktop: table. The header sticks, since a page holds up to
            100 rows and the column a number belongs to has to stay
            identifiable while scrolling.

            `sticky` resolves against the nearest scrolling ancestor, so
            every ancestor between the header and the page has to stay
            unclipped: `Card`'s `overflow-hidden` (relaxed above) and the
            primitive's container, set to `overflow: visible` here. That
            gives up the container's horizontal scroll, which the two
            cannot both have — per spec `overflow-y: visible` computes back
            to `auto` when the other axis scrolls, so there is no pairing
            that scrolls sideways and still lets the header escape. It
            costs nothing here: this layout is `md:` and up, where four
            columns fit, and the description cell truncates rather than
            forcing the table wider. The card list covers narrow screens. */}
        <div className="hidden border-t md:block [&>div]:overflow-visible">
          <Table>
            {/* Stuck per cell rather than on the <thead>: `Card` clips to its
                rounded corners, and a clipping ancestor stops a sticky
                <thead> from pinning to the viewport. The background goes on
                the cells for the same reason it has to be opaque — the rows
                scrolling underneath must not show through. */}
            <TableHeader className="**:data-[slot=table-head]:sticky **:data-[slot=table-head]:top-0 **:data-[slot=table-head]:z-10 **:data-[slot=table-head]:bg-muted">
              <TableRow className="hover:bg-transparent">
                {TRANSACTION_COLUMNS.map((column) => (
                  <SortableHeader
            key={column.id}
            column={column}
            sortBy={sortBy}
            sortOrder={sortOrder}
            isFetching={isFetching}
            onSort={handleSortColumn}
            />
            ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {isEmpty ? (
                <EmptyRow hasActiveFilters={hasActiveFilters} />
              ) : (
            transactions.map((transaction) => (
                  <TransactionRow
            key={`${transaction.account_id}-${transaction.transaction_id}`}
            transaction={transaction}
            account={accountsById.get(transaction.account_id)}
            density={density}
            onOpen={openDetail}
            />
            ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Mobile: the card layout has no header row to click, so sorting
            gets its own control. Hidden when there is nothing to sort. */}
        {!isEmpty && (
          <div className="flex items-center justify-between gap-3 border-t px-4 py-3 md:hidden">
            <span className="text-xs tracking-wider text-muted-foreground uppercase">
              Sort
            </span>
            <SortSelect
              sort={sortBy}
              dir={sortOrder}
              onSortChange={handleSortChange}
              className="w-[190px]"
            />
          </div>
        )}

        <div className="divide-y divide-border md:hidden">
          {isEmpty ? (
            <Empty className="border-0 py-12">
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <Inbox />
                </EmptyMedia>
                <EmptyTitle>No transactions found</EmptyTitle>
                <EmptyDescription>
                  {hasActiveFilters
            ? "Try adjusting your filters to see more results."
            : "No transactions are available for the selected criteria."}
                </EmptyDescription>
              </EmptyHeader>
            </Empty>
          ) : (
            transactions.map((transaction) => (
              <TransactionCard
            key={`${transaction.account_id}-${transaction.transaction_id}`}
            transaction={transaction}
            account={accountsById.get(transaction.account_id)}
            onOpen={openDetail}
              />
            ))
          )}
        </div>

        {pagination && (
          <div className="flex items-center border-t px-2">
            {/* Density sits beside the pagination controls rather than in the
            header — both are table-chrome, and the footer is where a
            reader already goes to change how much they see at once. */}
            <div className="hidden shrink-0 md:block">
              <DensityToggle
            density={density}
            onDensityChange={changeDensity}
              />
            </div>
            {/* Net for the rows on screen, in the registry's muted footer
            slot. Quiet by design — it describes this page, not a period,
            and it is a footnote to the table rather than a headline. */}
            {!isEmpty && (
              <span className="hidden shrink-0 pr-6 text-sm text-muted-foreground lg:inline">
            Net{" "}
                <BlurredValue>
                  <span className="tabular-nums">
                    {pageNet >= 0 ? "+" : "\u2212"}
                    {formatCurrency(Math.abs(pageNet), displayCurrency)}
                  </span>
                </BlurredValue>{" "}
            on this page
              </span>
            )}
            <DataTablePagination
              className="min-w-0 flex-1"
              currentPage={pagination.page}
              totalPages={pagination.total_pages}
              pageSize={pagination.per_page}
              total={pagination.total}
              hasNext={pagination.has_next}
              hasPrev={pagination.has_prev}
              onPageChange={setCurrentPage}
              onPageSizeChange={setPerPage}
            />
          </div>
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
