import { Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { DateRangePicker } from "./DateRangePicker";
import { AccountCombobox } from "./AccountCombobox";
import { ActiveFilterChips } from "./ActiveFilterChips";
import { AdvancedFiltersPopover } from "./AdvancedFiltersPopover";
import type { Account } from "../../types/api";

export interface FilterState {
  searchTerm: string;
  selectedAccount: string;
  startDate: string;
  endDate: string;
  minAmount: string;
  maxAmount: string;
}

export interface FilterBarProps {
  filterState: FilterState;
  onFilterChange: (key: keyof FilterState, value: string) => void;
  onClearFilters: () => void;
  accounts?: Account[];
  isSearchLoading?: boolean;
  className?: string;
}

export function FilterBar({
  filterState,
  onFilterChange,
  onClearFilters,
  accounts,
  isSearchLoading = false,
  className,
}: FilterBarProps) {
  const hasActiveFilters =
    filterState.searchTerm ||
    filterState.selectedAccount ||
    filterState.startDate ||
    filterState.endDate ||
    filterState.minAmount ||
    filterState.maxAmount;

  const handleDateRangeChange = (startDate: string, endDate: string) => {
    onFilterChange("startDate", startDate);
    onFilterChange("endDate", endDate);
  };

  return (
    <div className={cn("bg-card rounded-lg shadow border", className)}>
      {/* Main Filter Bar */}
      <div className="px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-card-foreground">
            Transactions
          </h3>
        </div>

        {/* Primary Filters Row */}
        <div className="flex flex-wrap items-center gap-3 mb-4">
          {/* Search Input */}
          <div className="relative flex-1 min-w-[240px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search transactions..."
              value={filterState.searchTerm}
              onChange={(e) => onFilterChange("searchTerm", e.target.value)}
              className="pl-9 pr-8 bg-background"
            />
            {isSearchLoading && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="animate-spin h-4 w-4 border-2 border-border border-t-primary rounded-full"></div>
              </div>
            )}
          </div>

          {/* Account Selection */}
          <AccountCombobox
            accounts={accounts}
            selectedAccount={filterState.selectedAccount}
            onAccountChange={(accountId) =>
              onFilterChange("selectedAccount", accountId)
            }
            className="w-[200px]"
          />

          {/* Date Range Picker */}
          <DateRangePicker
            startDate={filterState.startDate}
            endDate={filterState.endDate}
            onDateRangeChange={handleDateRangeChange}
            className="w-[240px]"
          />

          {/* Advanced Filters Button */}
          <AdvancedFiltersPopover
            minAmount={filterState.minAmount}
            maxAmount={filterState.maxAmount}
            onMinAmountChange={(value) => onFilterChange("minAmount", value)}
            onMaxAmountChange={(value) => onFilterChange("maxAmount", value)}
          />

          {/* Clear Filters Button */}
          {hasActiveFilters && (
            <Button
              onClick={onClearFilters}
              variant="outline"
              size="sm"
              className="text-muted-foreground"
            >
              <X className="h-4 w-4 mr-1" />
              Clear All
            </Button>
          )}
        </div>

        {/* Active Filter Chips */}
        {hasActiveFilters && (
          <ActiveFilterChips
            filterState={filterState}
            onFilterChange={onFilterChange}
            accounts={accounts}
          />
        )}
      </div>
    </div>
  );
}
