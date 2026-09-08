import { Skeleton } from "./ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { TRANSACTION_COLUMNS } from "./transactions/columns";
import { cn } from "@/lib/utils";
import {
  DENSITY_CELL_CLASS,
  DEFAULT_DENSITY,
  type Density,
} from "@/lib/density";

interface TransactionSkeletonProps {
  rows?: number;
  view?: "table" | "mobile";
  density?: Density;
}

/** Placeholder width per column, so the shapes suggest the real content. */
const CELL_SKELETON: Record<string, string> = {
  date: "w-24",
  description: "w-3/4",
  category: "w-20",
  amount: "w-24",
};

/**
 * Loading placeholder for the transaction list.
 *
 * Driven by `TRANSACTION_COLUMNS` and the same `Table` primitive as the real
 * thing, so it cannot fall out of step with it — the previous version
 * hand-rolled its own markup and had drifted to a different column order.
 */
export default function TransactionSkeleton({
  rows = 5,
  view = "table",
  density = DEFAULT_DENSITY,
}: TransactionSkeletonProps) {
  const skeletonRows = Array.from({ length: rows }, (_, index) => index);

  if (view === "mobile") {
    return (
      <div className="divide-y divide-border">
        {skeletonRows.map((index) => (
          <div key={index} className="p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
              <Skeleton className="h-5 w-20 shrink-0" />
            </div>
            <div className="mt-3 flex items-center justify-between">
              <Skeleton className="h-5 w-20" />
              <Skeleton className="h-3 w-16" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <Table>
      <TableHeader className="bg-muted/50">
        <TableRow className="hover:bg-transparent">
          {TRANSACTION_COLUMNS.map((column) => (
            <TableHead
              key={column.id}
              className={cn("px-4", column.className)}
            >
              <Skeleton className="h-4 w-16" />
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {skeletonRows.map((index) => (
          <TableRow key={index} className="hover:bg-transparent">
            {TRANSACTION_COLUMNS.map((column) => (
              <TableCell
                key={column.id}
                className={cn("px-4", DENSITY_CELL_CLASS[density])}
              >
                <Skeleton
                  className={cn(
                    "h-4",
                    CELL_SKELETON[column.id] ?? "w-16",
                    column.align === "right" && "ml-auto",
                  )}
                />
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
