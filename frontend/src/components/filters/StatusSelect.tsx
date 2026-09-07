import { CircleDot } from "lucide-react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

/**
 * Booked/pending filter.
 *
 * The URL and the API both spell "no filter" as an absent param, but Base
 * UI's Select needs a concrete value for its items, so the empty string is
 * used as the sentinel for "All statuses" and translated at the boundary.
 */
const ALL = "all";

export interface StatusSelectProps {
  selectedStatus: string;
  onStatusChange: (status: string) => void;
  className?: string;
}

export function StatusSelect({
  selectedStatus,
  onStatusChange,
  className,
}: StatusSelectProps) {
  return (
    <Select
      value={selectedStatus || ALL}
      onValueChange={(value) => onStatusChange(value === ALL ? "" : value)}
    >
      <SelectTrigger className={className} aria-label="Filter by status">
        <div className="flex items-center">
          <CircleDot className="mr-2 h-4 w-4 shrink-0 text-muted-foreground" />
          <SelectValue placeholder="All statuses" />
        </div>
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>All statuses</SelectItem>
        <SelectItem value="booked">Booked</SelectItem>
        <SelectItem value="pending">Pending</SelectItem>
      </SelectContent>
    </Select>
  );
}
