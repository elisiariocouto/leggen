import { ArrowUpDown } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type {
  SortDirection,
  TransactionSortField,
} from "@/lib/searchParams";

/**
 * Sort control for the mobile card layout, which has no table header to
 * click. Field and direction are one list of concrete choices rather than
 * two controls, since only a handful of the combinations are useful.
 */
export const SORT_OPTIONS: Array<{
  value: string;
  label: string;
  sort: TransactionSortField;
  dir: SortDirection;
}> = [
  { value: "date-desc", label: "Newest first", sort: "date", dir: "desc" },
  { value: "date-asc", label: "Oldest first", sort: "date", dir: "asc" },
  { value: "amount-asc", label: "Largest expense", sort: "amount", dir: "asc" },
  {
    value: "amount-desc",
    label: "Largest income",
    sort: "amount",
    dir: "desc",
  },
  {
    value: "description-asc",
    label: "Description (A–Z)",
    sort: "description",
    dir: "asc",
  },
];

export interface SortSelectProps {
  sort: TransactionSortField;
  dir: SortDirection;
  onSortChange: (sort: TransactionSortField, dir: SortDirection) => void;
  className?: string;
}

export function SortSelect({
  sort,
  dir,
  onSortChange,
  className,
}: SortSelectProps) {
  const current =
    SORT_OPTIONS.find((option) => option.sort === sort && option.dir === dir) ??
    SORT_OPTIONS[0];

  return (
    <Select
      value={current.value}
      onValueChange={(value) => {
        const next = SORT_OPTIONS.find((option) => option.value === value);
        if (next) onSortChange(next.sort, next.dir);
      }}
    >
      <SelectTrigger className={className} aria-label="Sort transactions">
        <ArrowUpDown className="mr-2 h-4 w-4 shrink-0 text-muted-foreground" />
        {/* Base UI renders the raw value unless given a render function, and
            "amount-asc" is not what the trigger should read. */}
        <SelectValue render={() => <span>{current.label}</span>} />
      </SelectTrigger>
      <SelectContent>
        {SORT_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
