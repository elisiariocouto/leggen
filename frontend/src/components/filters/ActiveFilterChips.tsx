import { X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { accountLabel, formatDate } from "@/lib/utils";
import { describeRange } from "@/lib/dateRanges";
import type { FilterState } from "./FilterBar";
import type { Account } from "../../types/api";
import { useCategories } from "../../hooks/queries";

export interface ActiveFilterChipsProps {
  filterState: FilterState;
  onFilterChange: (key: keyof FilterState, value: string) => void;
  onClearFilters: () => void;
  accounts?: Account[];
}

export function ActiveFilterChips({
  filterState,
  onFilterChange,
  onClearFilters,
  accounts = [],
}: ActiveFilterChipsProps) {
  const { data: categories } = useCategories({
    enabled: !!filterState.selectedCategory,
  });

  const chips: Array<{
    key: keyof FilterState;
    label: string;
    value: string;
  }> = [];

  // Search term chip
  if (filterState.searchTerm) {
    chips.push({
      key: "searchTerm",
      label: `Search: "${filterState.searchTerm}"`,
      value: filterState.searchTerm,
    });
  }

  // Account chip
  if (filterState.selectedAccount) {
    const account = accounts.find(
      (acc) => acc.id === filterState.selectedAccount,
    );
    const accountName = account
      ? `${accountLabel(account)} (${account.institution_id})`
      : "Unknown Account";
    chips.push({
      key: "selectedAccount",
      label: accountName,
      value: filterState.selectedAccount,
    });
  }

  // Category chip
  if (filterState.selectedCategory) {
    let categoryLabel = "Category: ";
    if (filterState.selectedCategory === "uncategorized") {
      categoryLabel += "Uncategorized";
    } else {
      const category = categories?.find(
        (cat) => String(cat.id) === filterState.selectedCategory,
      );
      categoryLabel += category?.name || `ID ${filterState.selectedCategory}`;
    }
    chips.push({
      key: "selectedCategory",
      label: categoryLabel,
      value: filterState.selectedCategory,
    });
  }

  // Status chip
  if (filterState.selectedStatus) {
    chips.push({
      key: "selectedStatus",
      label: `Status: ${
        filterState.selectedStatus.charAt(0).toUpperCase() +
        filterState.selectedStatus.slice(1)
      }`,
      value: filterState.selectedStatus,
    });
  }

  if (filterState.selectedKind) {
    chips.push({
      key: "selectedKind",
      label: filterState.selectedKind === "income" ? "Income only" : "Expenses only",
      value: filterState.selectedKind,
    });
  }

  // Date range chip
  if (filterState.startDate || filterState.endDate) {
    let dateLabel = "Date: ";
    if (filterState.startDate && filterState.endDate) {
      dateLabel += describeRange(filterState.startDate, filterState.endDate);
    } else if (filterState.startDate) {
      dateLabel += `From ${formatDate(filterState.startDate)}`;
    } else if (filterState.endDate) {
      dateLabel += `Until ${formatDate(filterState.endDate)}`;
    }

    chips.push({
      key: "startDate", // We'll clear both start and end date when removing this chip
      label: dateLabel,
      value: `${filterState.startDate}-${filterState.endDate}`,
    });
  }

  if (filterState.minAmount || filterState.maxAmount) {
    const from = filterState.minAmount || "0";
    const to = filterState.maxAmount || "∞";
    chips.push({
      // Clears both bounds, like the combined date chip above.
      key: "minAmount",
      label: `Amount: ${from} - ${to}`,
      value: `${filterState.minAmount}-${filterState.maxAmount}`,
    });
  }

  const handleRemoveChip = (key: keyof FilterState) => {
    switch (key) {
      case "startDate":
        // Clear both start and end date
        onFilterChange("startDate", "");
        onFilterChange("endDate", "");
        break;
      case "minAmount":
        // Clear both amount bounds
        onFilterChange("minAmount", "");
        onFilterChange("maxAmount", "");
        break;
      default:
        onFilterChange(key, "");
    }
  };

  if (chips.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-muted-foreground font-medium">Active filters:</span>
      {chips.map((chip) => (
        <Badge
          key={`${chip.key}-${chip.value}`}
          variant="secondary"
          className="pl-3 pr-1 py-1 bg-primary/10 text-primary border-primary/20 hover:bg-primary/20"
        >
          <span className="mr-1 text-xs">{chip.label}</span>
          <Button
            variant="ghost"
            size="sm"
            className="h-4 w-4 p-0 hover:bg-primary/20"
            onClick={() => handleRemoveChip(chip.key)}
          >
            <X className="h-3 w-3" />
            <span className="sr-only">Remove {chip.label} filter</span>
          </Button>
        </Badge>
      ))}
      <Button
        onClick={onClearFilters}
        variant="outline"
        size="sm"
        className="text-muted-foreground ml-2"
      >
        <X className="h-4 w-4 mr-1" />
        Clear All
      </Button>
    </div>
  );
}
