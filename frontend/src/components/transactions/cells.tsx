import { formatCurrency, formatDate } from "@/lib/utils";
import { BlurredValue } from "@/components/ui/blurred-value";
import CategoryBadge from "@/components/CategoryBadge";
import TransactionStatusBadge from "@/components/TransactionStatusBadge";
import type { Account, Transaction } from "@/types/api";

/**
 * The pieces a transaction row is built from.
 *
 * Both layouts — the desktop table and the mobile card list — render from
 * these, so an amount is styled once and a category behaves the same way in
 * either. Previously the card list inlined its own copy of each.
 */

export function isIncome(transaction: Transaction): boolean {
  return transaction.transaction_value > 0;
}

/**
 * Signed, coloured amount.
 *
 * The sign and the colour already carry the direction, which is why there is
 * no longer an arrow icon beside it — that was a third encoding of the same
 * bit, and it cost ~48px of row width.
 */
export function Amount({
  transaction,
  className,
}: {
  transaction: Transaction;
  className?: string;
}) {
  const positive = isIncome(transaction);
  return (
    <span
      className={`font-semibold tabular-nums ${
        positive ? "text-positive" : "text-negative"
      } ${className ?? ""}`}
    >
      <BlurredValue>
        {positive ? "+" : ""}
        {formatCurrency(
          transaction.transaction_value,
          transaction.transaction_currency,
        )}
      </BlurredValue>
    </span>
  );
}

export function TransactionCategory({
  transaction,
}: {
  transaction: Transaction;
}) {
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

export function transactionDate(transaction: Transaction): string {
  return transaction.transaction_date
    ? formatDate(transaction.transaction_date)
    : "No date";
}

export function accountName(account: Account | undefined): string | null {
  if (!account) return null;
  return account.display_name || "Unnamed Account";
}

/**
 * Description plus the secondary line under it (account, and a chip when the
 * transaction is still pending). Booked is the norm and says nothing useful,
 * so only the exceptions are marked.
 */
export function Description({
  transaction,
  account,
  wrap = false,
}: {
  transaction: Transaction;
  account: Account | undefined;
  wrap?: boolean;
}) {
  const name = accountName(account);
  return (
    <div className="min-w-0">
      <div
        className={`text-sm font-medium text-foreground ${
          wrap ? "wrap-break-word" : "truncate"
        }`}
      >
        {transaction.description}
      </div>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {name && <span className={wrap ? "" : "truncate"}>{name}</span>}
        <TransactionStatusBadge
          status={transaction.transaction_status}
          pendingOnly
          className="shrink-0"
        />
      </div>
    </div>
  );
}

/** Accessible label for the row/card control that opens the detail panel. */
export function openDetailLabel(transaction: Transaction): string {
  return `Transaction ${transaction.description}, ${formatCurrency(
    transaction.transaction_value,
    transaction.transaction_currency,
  )}. Open details`;
}

/**
 * Enter/Space activation for a row or card.
 *
 * Guarded on the event target so a keypress inside a nested control — the
 * category popover, most importantly — does not also open the panel.
 */
export function handleActivateKeyDown(
  event: React.KeyboardEvent,
  activate: () => void,
): void {
  if (event.target !== event.currentTarget) return;
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    activate();
  }
}
