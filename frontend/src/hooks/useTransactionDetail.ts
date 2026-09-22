import { useState } from "react";
import type { Transaction } from "@/types/api";

/**
 * State for a transaction detail panel opened from a list.
 *
 * The panel shows the list's live copy of the row, so a category change made
 * while it is open (which refetches the list) shows up in it too. It falls
 * back to the snapshot taken when it was opened: the row leaves the page if
 * a category filter is active and it was just recategorized, and it is also
 * gone during the closing animation.
 */
export function useTransactionDetail(transactions: Transaction[]) {
  const [open, setOpen] = useState(false);
  const [snapshot, setSnapshot] = useState<Transaction | null>(null);

  const live = snapshot
    ? transactions.find(
        (t) =>
          t.account_id === snapshot.account_id &&
          t.transaction_id === snapshot.transaction_id,
      )
    : undefined;
  const transaction = live ?? snapshot;

  return {
    /** Props for `TransactionDetail`. */
    panel: {
      transaction,
      open: open && transaction !== null,
      onOpenChange: setOpen,
    },
    openDetail: (row: Transaction) => {
      setSnapshot(row);
      setOpen(true);
    },
  };
}
