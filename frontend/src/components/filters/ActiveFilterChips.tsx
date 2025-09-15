import { X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";
import type { FilterState } from "./FilterBar";
import type { Account } from "../../types/api";

export interface ActiveFilterChipsProps {
  filterState: FilterState;
  onFilterChange: (key: keyof FilterState, value: string) => void;
  accounts?: Account[];
}

export function ActiveFilterChips({
  filterState,
  onFilterChange,
  accounts = [],
}: ActiveFilterChipsProps) {
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
      ? `${account.name || "Unnamed Account"} (${account.institution_id})`
      : "Unknown Account";
    chips.push({
      key: "selectedAccount",
      label: accountName,
      value: filterState.selectedAccount,
    });
  }

  // Date range chip
  if (filterState.startDate || filterState.endDate) {
    let dateLabel = "Date: ";
    if (filterState.startDate && filterState.endDate) {
      if (filterState.startDate === filterState.endDate) {
        dateLabel += formatDate(filterState.startDate);
      } else {
        dateLabel += `${formatDate(filterState.startDate)} - ${formatDate(filterState.endDate)}`;
      }
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

  // Amount range chips
  if (filterState.minAmount || filterState.maxAmount) {
    let amountLabel = "Amount: ";
    const minAmount = filterState.minAmount
      ? parseFloat(filterState.minAmount)
      : null;
    const maxAmount = filterState.maxAmount
      ? parseFloat(filterState.maxAmount)
      : null;

    if (minAmount && maxAmount) {
      amountLabel += `€${minAmount} - €${maxAmount}`;
    } else if (minAmount) {
      amountLabel += `≥ €${minAmount}`;
    } else if (maxAmount) {
      amountLabel += `≤ €${maxAmount}`;
    }

    chips.push({
      key: "minAmount", // We'll clear both min and max when removing this chip
      label: amountLabel,
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
        // Clear both min and max amount
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
      <span className="text-sm text-gray-600 font-medium">Active filters:</span>
      {chips.map((chip) => (
        <Badge
          key={`${chip.key}-${chip.value}`}
          variant="secondary"
          className="pl-3 pr-1 py-1 bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100"
        >
          <span className="mr-1 text-xs">{chip.label}</span>
          <Button
            variant="ghost"
            size="sm"
            className="h-4 w-4 p-0 hover:bg-blue-200/50"
            onClick={() => handleRemoveChip(chip.key)}
          >
            <X className="h-3 w-3" />
            <span className="sr-only">Remove {chip.label} filter</span>
          </Button>
        </Badge>
      ))}
    </div>
  );
}
