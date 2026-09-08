import { TableCell, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { handleActivateKeyDown, openDetailLabel } from "./cells";
import { TRANSACTION_COLUMNS } from "./columns";
import { DENSITY_CELL_CLASS, type Density } from "@/lib/density";
import type { Account, Transaction } from "@/types/api";

/**
 * One transaction as a table row.
 *
 * The row itself is the control that opens the detail panel, so it is
 * focusable and activatable from the keyboard rather than relying on a
 * click target inside it.
 */
export default function TransactionRow({
  transaction,
  account,
  density,
  onOpen,
}: {
  transaction: Transaction;
  account: Account | undefined;
  density: Density;
  onOpen: (transaction: Transaction) => void;
}) {
  return (
    <TableRow
      className="cursor-pointer focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset focus-visible:outline-hidden"
      tabIndex={0}
      aria-label={openDetailLabel(transaction)}
      onClick={() => onOpen(transaction)}
      onKeyDown={(event) =>
        handleActivateKeyDown(event, () => onOpen(transaction))
      }
    >
      {TRANSACTION_COLUMNS.map((column) => (
        <TableCell
          key={column.id}
          className={cn(
            "px-4",
            DENSITY_CELL_CLASS[density],
            column.align === "right" && "text-right",
            column.className,
          )}
          onClick={
            column.stopRowActivation
              ? (event) => event.stopPropagation()
              : undefined
          }
        >
          {column.cell(transaction, { account })}
        </TableCell>
      ))}
    </TableRow>
  );
}
