import { useState } from "react";
import { MoreHorizontal, Euro } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

export interface AdvancedFiltersPopoverProps {
  minAmount: string;
  maxAmount: string;
  onMinAmountChange: (value: string) => void;
  onMaxAmountChange: (value: string) => void;
}

export function AdvancedFiltersPopover({
  minAmount,
  maxAmount,
  onMinAmountChange,
  onMaxAmountChange,
}: AdvancedFiltersPopoverProps) {
  const [open, setOpen] = useState(false);

  const hasAdvancedFilters = minAmount || maxAmount;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant={hasAdvancedFilters ? "default" : "outline"}
          size="default"
          className="relative"
        >
          <MoreHorizontal className="h-4 w-4 mr-2" />
          More
          {hasAdvancedFilters && (
            <div className="absolute -top-1 -right-1 h-2 w-2 bg-blue-600 rounded-full" />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="end">
        <div className="space-y-4">
          <div className="space-y-2">
            <h4 className="font-medium leading-none">Advanced Filters</h4>
            <p className="text-sm text-muted-foreground">
              Additional filters for more precise results
            </p>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Amount Range
              </label>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">
                    Minimum
                  </label>
                  <div className="relative">
                    <Euro className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      type="number"
                      placeholder="0.00"
                      value={minAmount}
                      onChange={(e) => onMinAmountChange(e.target.value)}
                      className="pl-8"
                      step="0.01"
                      min="0"
                    />
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">
                    Maximum
                  </label>
                  <div className="relative">
                    <Euro className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      type="number"
                      placeholder="1000.00"
                      value={maxAmount}
                      onChange={(e) => onMaxAmountChange(e.target.value)}
                      className="pl-8"
                      step="0.01"
                      min="0"
                    />
                  </div>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Leave empty for no limit
              </p>
            </div>

            {/* Future: Add transaction status filter */}
            <div className="pt-2 border-t">
              <div className="text-xs text-muted-foreground">
                More filters coming soon: transaction status, categories, and more.
              </div>
            </div>

            {/* Clear advanced filters */}
            {hasAdvancedFilters && (
              <div className="pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    onMinAmountChange("");
                    onMaxAmountChange("");
                  }}
                  className="w-full"
                >
                  Clear Advanced Filters
                </Button>
              </div>
            )}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
