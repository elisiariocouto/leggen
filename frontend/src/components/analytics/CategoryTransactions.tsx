import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { formatCurrency } from "../../lib/utils";
import { BlurredValue } from "../ui/blurred-value";
import { Skeleton } from "../ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "../ui/sheet";
import TransactionDetail from "../TransactionDetail";
import {
  Amount,
  Description,
  handleActivateKeyDown,
  openDetailLabel,
  transactionDate,
} from "../transactions/cells";
import apiClient from "../../lib/api";
import { queryKeys } from "../../lib/queryKeys";
import type { Transaction } from "../../types/api";
import { useAccounts } from "../../hooks/queries";

/** The API caps a page here; a single month of one category rarely nears it. */
const PAGE_SIZE = 500;

/**
 * One cell of the category matrix: a category (or every category) over a
 * date range. The label and figure come from the matrix so the panel opens
 * with the numbers the reader just clicked, before the list has loaded.
 */
export interface CellSelection {
  /** A category id, null for uncategorized spend, undefined for every category. */
  categoryId: number | null | undefined;
  categoryName: string;
  categoryColor: string;
  from: string;
  to: string;
  /** "Sep 2025", or the whole period. */
  periodLabel: string;
  total: number;
  currency: string;
}

interface CategoryTransactionsProps {
  selection: CellSelection | undefined;
  onClose: () => void;
  accountId?: string;
}

/** The transactions route's category filter for a selection. */
function filterIdOf(selection: CellSelection): string | undefined {
  if (selection.categoryId === undefined) return undefined;
  return selection.categoryId === null
    ? "uncategorized"
    : String(selection.categoryId);
}

/**
 * The transactions behind one figure of the matrix, listed in a panel so
 * the reader can check a month without leaving the page. A row opens the
 * transaction's own detail panel; the link at the bottom opens the same
 * set in the transactions table with its filters already applied.
 */
export default function CategoryTransactions({
  selection,
  onClose,
  accountId,
}: CategoryTransactionsProps) {
  const open = selection !== undefined;
  const filterId = selection ? filterIdOf(selection) : undefined;

  const [detail, setDetail] = useState<Transaction | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const { data: accounts } = useAccounts({ enabled: open });

  const { data, isLoading } = useQuery({
    // Under the transactions root so a recategorisation from the detail
    // panel refreshes this list along with the table.
    queryKey: queryKeys.transactionList({
      accountId: accountId ?? "",
      categoryId: filterId ?? "",
      startDate: selection?.from ?? "",
      endDate: selection?.to ?? "",
      status: "",
      kind: "expense",
      page: 1,
      perPage: PAGE_SIZE,
      search: "",
      minAmount: undefined,
      maxAmount: undefined,
      sortBy: "date",
      sortOrder: "desc",
    }),
    queryFn: () =>
      apiClient.getTransactions({
        accountId,
        startDate: selection!.from,
        endDate: selection!.to,
        categoryId: filterId,
        kind: "expense",
        page: 1,
        perPage: PAGE_SIZE,
        summaryOnly: false,
        sortBy: "date",
        sortOrder: "desc",
      }),
    enabled: open,
  });

  const accountsById = useMemo(
    () => new Map((accounts ?? []).map((account) => [account.id, account])),
    [accounts],
  );

  const transactions = data?.data ?? [];
  // Prefer the live row so an edit made in the detail panel shows up there
  // too, and fall back to the snapshot during the closing animation.
  const selectedTransaction =
    transactions.find(
      (t) =>
        t.account_id === detail?.account_id &&
        t.transaction_id === detail?.transaction_id,
    ) ?? detail;

  const openDetail = (transaction: Transaction) => {
    setDetail(transaction);
    setDetailOpen(true);
  };

  return (
    <Sheet open={open} onOpenChange={(next) => !next && onClose()}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-xl overflow-y-auto"
      >
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <span
              className="h-3 w-3 rounded-full shrink-0"
              style={{ backgroundColor: selection?.categoryColor }}
            />
            {selection?.categoryName ?? "Category"}
          </SheetTitle>
          <SheetDescription>
            {selection ? (
              <>
                {selection.periodLabel}
                {" · "}
                <BlurredValue>
                  {formatCurrency(selection.total, selection.currency)}
                </BlurredValue>
                {data && (
                  <>
                    {" · "}
                    {data.total} {data.total === 1 ? "expense" : "expenses"}
                  </>
                )}
              </>
            ) : (
              "Expenses in this category over the selected month"
            )}
          </SheetDescription>
        </SheetHeader>

        {selection && (
          <div className="px-4 pb-6 space-y-4">
            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 6 }, (_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : transactions.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                No expenses found
              </p>
            ) : (
              <ul className="divide-y rounded-md border">
                {transactions.map((transaction) => (
                  <li
                    key={`${transaction.account_id}:${transaction.transaction_id}`}
                    className="flex items-start justify-between gap-3 px-3 py-2.5 cursor-pointer transition-colors hover:bg-muted/50 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset focus-visible:outline-hidden"
                    role="button"
                    tabIndex={0}
                    aria-label={openDetailLabel(transaction)}
                    onClick={() => openDetail(transaction)}
                    onKeyDown={(event) =>
                      handleActivateKeyDown(event, () => openDetail(transaction))
                    }
                  >
                    <Description
                      transaction={transaction}
                      account={accountsById.get(transaction.account_id)}
                    />
                    <div className="shrink-0 text-right">
                      <Amount transaction={transaction} className="text-sm" />
                      <div className="text-xs text-muted-foreground">
                        {transactionDate(transaction)}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            {data?.has_next && (
              <p className="text-xs text-muted-foreground">
                Showing the first {transactions.length} of {data.total}. The
                transactions table has the rest.
              </p>
            )}

            <Link
              to="/transactions"
              search={{
                category: filterId,
                kind: "expense",
                from: selection.from,
                to: selection.to,
                account: accountId,
              }}
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              Open in the transactions table
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        )}

        {/* Rendered inside the sheet so the dialog library treats it as a
            nested dialog rather than a click outside this one. */}
        <TransactionDetail
          transaction={selectedTransaction}
          open={detailOpen && !!selectedTransaction}
          onOpenChange={setDetailOpen}
          accounts={accounts}
        />
      </SheetContent>
    </Sheet>
  );
}
