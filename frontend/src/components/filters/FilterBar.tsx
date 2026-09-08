import { useRef } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { DateRangePicker } from "./DateRangePicker";
import type { DatePreset } from "./DateRangePicker";
import { AccountCombobox } from "./AccountCombobox";
import { CategoryCombobox } from "./CategoryCombobox";
import { StatusSelect } from "./StatusSelect";
import { AmountRangeFilter } from "./AmountRangeFilter";
import { ActiveFilterChips } from "./ActiveFilterChips";
import { TIME_PERIODS } from "../../lib/timePeriods";
import type { Account } from "../../types/api";

const transactionPresets: DatePreset[] = TIME_PERIODS.map((p) => ({
  label: p.label,
  getValue: p.getDateRange,
}));

export interface FilterState {
  searchTerm: string;
  selectedAccount: string;
  selectedCategory: string;
  selectedStatus: string;
  startDate: string;
  endDate: string;
  // Kept as strings like every other field ("" means unset) so the whole
  // shape stays uniform; parsed to numbers at the API boundary.
  minAmount: string;
  maxAmount: string;
}

export interface FilterBarProps {
  filterState: FilterState;
  onFilterChange: (key: keyof FilterState, value: string) => void;
  onClearFilters: () => void;
  accounts?: Account[];
  isSearchLoading?: boolean;
  /** Labels the amount inputs; the dominant currency of the current set. */
  currency?: string;
  className?: string;
}

export function FilterBar({
  filterState,
  onFilterChange,
  onClearFilters,
  accounts,
  isSearchLoading = false,
  currency,
  className,
}: FilterBarProps) {
  const searchInputRef = useRef<HTMLInputElement>(null);

  const hasActiveFilters =
    filterState.searchTerm ||
    filterState.selectedAccount ||
    filterState.selectedCategory ||
    filterState.selectedStatus ||
    filterState.startDate ||
    filterState.endDate ||
    filterState.minAmount ||
    filterState.maxAmount;

  const handleDateRangeChange = (startDate: string, endDate: string) => {
    onFilterChange("startDate", startDate);
    onFilterChange("endDate", endDate);
  };

  return (
    <div className={cn("px-6 py-4", className)}>
      {/* Primary Filters Row */}
      <div className={cn("space-y-4", hasActiveFilters && "mb-4")}>
        {/* Desktop Layout */}
        <div className="hidden lg:flex items-center justify-between gap-6">
          {/* Left Side: Search & Account */}
          <div className="flex items-center gap-3">
            <div className="relative w-[300px]">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                ref={searchInputRef}
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

            <AccountCombobox
              accounts={accounts?.filter(
                (a) => a.status.toLowerCase() !== "deleted",
              )}
              selectedAccount={filterState.selectedAccount}
              onAccountChange={(accountId) =>
                onFilterChange("selectedAccount", accountId)
              }
              className="w-[180px]"
            />

            <CategoryCombobox
              selectedCategory={filterState.selectedCategory}
              onCategoryChange={(categoryId) =>
                onFilterChange("selectedCategory", categoryId)
              }
              className="w-[180px]"
            />

            <StatusSelect
              selectedStatus={filterState.selectedStatus}
              onStatusChange={(status) =>
                onFilterChange("selectedStatus", status)
              }
              className="w-[150px]"
            />

            <AmountRangeFilter
              minAmount={filterState.minAmount}
              maxAmount={filterState.maxAmount}
              onAmountChange={onFilterChange}
              currency={currency}
              className="w-[150px]"
            />
          </div>

          {/* Right Side: Date Range */}
          <DateRangePicker
            startDate={filterState.startDate}
            endDate={filterState.endDate}
            onDateRangeChange={handleDateRangeChange}
            presets={transactionPresets}
            className="w-[220px]"
          />
        </div>

        {/* Mobile Layout */}
        <div className="lg:hidden space-y-3">
          {/* First Row: Search Input (Full Width) */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              ref={searchInputRef}
              placeholder="Search..."
              value={filterState.searchTerm}
              onChange={(e) => onFilterChange("searchTerm", e.target.value)}
              className="pl-9 pr-8 bg-background w-full"
            />
            {isSearchLoading && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="animate-spin h-4 w-4 border-2 border-border border-t-primary rounded-full"></div>
              </div>
            )}
          </div>

          {/* Second Row: Account Selection (Full Width) */}
          <AccountCombobox
            accounts={accounts?.filter(
              (a) => a.status.toLowerCase() !== "deleted",
            )}
            selectedAccount={filterState.selectedAccount}
            onAccountChange={(accountId) =>
              onFilterChange("selectedAccount", accountId)
            }
            className="w-full"
          />

          {/* Third Row: Category Selection (Full Width) */}
          <CategoryCombobox
            selectedCategory={filterState.selectedCategory}
            onCategoryChange={(categoryId) =>
              onFilterChange("selectedCategory", categoryId)
            }
            className="w-full"
          />

          {/* Fourth Row: Status (Full Width) */}
          <StatusSelect
            selectedStatus={filterState.selectedStatus}
            onStatusChange={(status) => onFilterChange("selectedStatus", status)}
            className="w-full"
          />

          {/* Fifth Row: Amount range (Full Width) */}
          <AmountRangeFilter
            minAmount={filterState.minAmount}
            maxAmount={filterState.maxAmount}
            onAmountChange={onFilterChange}
            currency={currency}
            className="w-full"
          />

          {/* Sixth Row: Date Range */}
          <DateRangePicker
            startDate={filterState.startDate}
            endDate={filterState.endDate}
            onDateRangeChange={handleDateRangeChange}
            presets={transactionPresets}
            className="w-full"
          />
        </div>
      </div>

      {/* Active Filter Chips */}
      {hasActiveFilters && (
        <ActiveFilterChips
          filterState={filterState}
          onFilterChange={onFilterChange}
          onClearFilters={onClearFilters}
          accounts={accounts}
        />
      )}
    </div>
  );
}
