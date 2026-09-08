import { ArrowDown, ArrowUp, ArrowUpDown, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { TableHead } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { TransactionColumn } from "./columns";
import type { SortDirection, TransactionSortField } from "@/lib/searchParams";

/**
 * Sort arrow for a column header.
 *
 * `placeholderData` keeps the previous rows on screen while a re-sort is in
 * flight, so without a pending state the table would sit in the old order
 * with nothing to show the click registered.
 */
function SortIndicator({
  isSorted,
  direction,
  isPending,
}: {
  isSorted: boolean;
  direction: SortDirection;
  isPending: boolean;
}) {
  if (isPending) {
    return <Loader2 className="h-3 w-3 animate-spin" aria-label="Sorting" />;
  }
  if (!isSorted) {
    return <ArrowUpDown className="h-3 w-3 opacity-40" aria-hidden="true" />;
  }
  return direction === "asc" ? (
    <ArrowUp className="h-3 w-3" aria-hidden="true" />
  ) : (
    <ArrowDown className="h-3 w-3" aria-hidden="true" />
  );
}

/**
 * A column's header cell, clickable when the API can sort by it.
 *
 * `aria-sort` announces the state to screen readers — the arrow alone is
 * only available visually.
 */
export default function SortableHeader({
  column,
  sortBy,
  sortOrder,
  isFetching,
  onSort,
}: {
  column: TransactionColumn;
  sortBy: TransactionSortField;
  sortOrder: SortDirection;
  isFetching: boolean;
  onSort: (column: TransactionSortField) => void;
}) {
  const isSorted = column.sortKey === sortBy;

  return (
    <TableHead
      scope="col"
      aria-sort={
        isSorted
          ? sortOrder === "asc"
            ? "ascending"
            : "descending"
          : undefined
      }
      className={cn(
        "px-4 text-xs font-medium tracking-wider text-muted-foreground uppercase",
        column.align === "right" && "text-right",
        column.className,
      )}
    >
      {column.sortKey ? (
        // `Button variant="ghost"` rather than a bare <button>: it already
        // carries the hover, focus-ring and disabled treatment the rest of
        // the UI uses, which a hand-rolled control has to re-approximate.
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onSort(column.sortKey!)}
          className={cn(
            "-mx-2 h-8 gap-1 px-2 text-xs font-medium tracking-wider text-muted-foreground uppercase hover:text-foreground",
            column.align === "right" && "flex-row-reverse",
            isSorted && "text-foreground",
          )}
        >
          {column.label}
          <SortIndicator
            isSorted={isSorted}
            direction={sortOrder}
            isPending={isSorted && isFetching}
          />
        </Button>
      ) : (
        column.label
      )}
    </TableHead>
  );
}
