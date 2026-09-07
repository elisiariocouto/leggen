import { Clock } from "lucide-react";

import { Badge } from "./ui/badge";
import { cn } from "@/lib/utils";

/**
 * Status chip for a transaction, shared by the table and the detail panel so
 * "pending" reads the same amber wherever it appears.
 *
 * `booked` is the overwhelmingly common case and carries no information the
 * reader needs, so the table asks for `pendingOnly` and renders nothing for
 * it — only the exceptions get a chip.
 */
export default function TransactionStatusBadge({
  status,
  pendingOnly = false,
  className,
}: {
  status: string;
  pendingOnly?: boolean;
  className?: string;
}) {
  const normalized = status?.toLowerCase() ?? "";

  if (normalized === "pending") {
    return (
      <Badge
        variant="outline"
        className={cn(
          "border-amber-500/50 text-amber-600 dark:text-amber-400",
          className,
        )}
      >
        <Clock className="mr-1 h-3 w-3" />
        Pending
      </Badge>
    );
  }

  if (pendingOnly) return null;

  if (normalized === "booked") {
    return (
      <Badge variant="secondary" className={className}>
        Booked
      </Badge>
    );
  }

  return (
    <Badge variant="secondary" className={className}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
}
