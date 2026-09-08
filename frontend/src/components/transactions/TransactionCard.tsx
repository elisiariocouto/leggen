import {
  Amount,
  Description,
  TransactionCategory,
  handleActivateKeyDown,
  openDetailLabel,
  transactionDate,
} from "./cells";
import type { Account, Transaction } from "@/types/api";

/**
 * One transaction as a card, for the mobile layout where four columns do not
 * fit. Built from the same cell pieces as the table row, so an amount or a
 * category cannot drift between the two layouts.
 */
export default function TransactionCard({
  transaction,
  account,
  onOpen,
}: {
  transaction: Transaction;
  account: Account | undefined;
  onOpen: (transaction: Transaction) => void;
}) {
  return (
    <div
      className="cursor-pointer p-4 transition-colors hover:bg-muted/50 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset focus-visible:outline-hidden"
      role="button"
      tabIndex={0}
      aria-label={openDetailLabel(transaction)}
      onClick={() => onOpen(transaction)}
      onKeyDown={(event) =>
        handleActivateKeyDown(event, () => onOpen(transaction))
      }
    >
      <div className="flex items-start justify-between gap-3">
        <Description transaction={transaction} account={account} wrap />
        <Amount transaction={transaction} className="shrink-0 text-base" />
      </div>
      <div className="mt-2 flex items-center justify-between gap-2">
        <div
          // Keep category popover interactions from opening the detail panel.
          onClick={(event) => event.stopPropagation()}
        >
          <TransactionCategory transaction={transaction} />
        </div>
        <span className="text-xs text-muted-foreground">
          {transactionDate(transaction)}
        </span>
      </div>
    </div>
  );
}
