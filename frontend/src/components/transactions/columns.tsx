import type { ReactNode } from "react";

import {
  Amount,
  Description,
  TransactionCategory,
  transactionDate,
} from "./cells";
import type { Account, Transaction } from "@/types/api";
import type { TransactionSortField } from "@/lib/searchParams";

/** What a cell renderer is given beyond the transaction itself. */
export interface CellContext {
  account: Account | undefined;
}

export interface TransactionColumn {
  id: string;
  label: string;
  /**
   * The API's sort field. A column without one is not sortable — Category
   * comes from a join and the API exposes no sort field for it, so making
   * the header clickable would promise an ordering the backend cannot serve.
   */
  sortKey?: TransactionSortField;
  align?: "right";
  /** Extra classes for both the header cell and the body cells. */
  className?: string;
  /**
   * Interactions inside this column must not bubble up to the row, which is
   * itself the control that opens the detail panel. Set for the category
   * column, whose badge opens a popover.
   */
  stopRowActivation?: boolean;
  cell: (transaction: Transaction, context: CellContext) => ReactNode;
}

/**
 * The table's columns, each carrying the cell it describes.
 *
 * Header and cell used to live ~100 lines apart, the body rendering them
 * positionally; a column is now one entry here and nothing else.
 */
export const TRANSACTION_COLUMNS: TransactionColumn[] = [
  {
    id: "date",
    label: "Date",
    sortKey: "date",
    // Leads the row: it is the default sort, so it is the column the eye
    // uses to navigate the list.
    className: "w-px whitespace-nowrap text-muted-foreground",
    cell: (transaction) => transactionDate(transaction),
  },
  {
    id: "description",
    label: "Description",
    sortKey: "description",
    // Description takes the slack so the other three sit at their natural
    // widths instead of drifting apart across the row.
    className: "w-full max-w-0",
    cell: (transaction, { account }) => (
      <Description transaction={transaction} account={account} />
    ),
  },
  {
    id: "category",
    label: "Category",
    stopRowActivation: true,
    cell: (transaction) => <TransactionCategory transaction={transaction} />,
  },
  {
    id: "amount",
    label: "Amount",
    sortKey: "amount",
    align: "right",
    // Trailing column: keep it off the table's right edge.
    className: "w-px pr-6 whitespace-nowrap",
    cell: (transaction) => <Amount transaction={transaction} />,
  },
];
