import { Coins } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

/**
 * Filters by how large a transaction is, ignoring its sign.
 *
 * The app shows expenses as positive figures, so a range of 40–50 is meant
 * to catch a 45 payment and a 45 refund alike — filtering on the signed
 * value would instead exclude every expense from a positive lower bound.
 */
export interface AmountRangeFilterProps {
  minAmount: string;
  maxAmount: string;
  onAmountChange: (key: "minAmount" | "maxAmount", value: string) => void;
  currency?: string;
  className?: string;
}

export function AmountRangeFilter({
  minAmount,
  maxAmount,
  onAmountChange,
  currency = "EUR",
  className,
}: AmountRangeFilterProps) {
  const hasRange = Boolean(minAmount || maxAmount);

  const label = hasRange
    ? `${minAmount || "0"} – ${maxAmount || "∞"}`
    : "Amount";

  return (
    <Popover>
      <PopoverTrigger
        render={
          <Button
            variant="outline"
            className={cn(
              "justify-start font-normal",
              !hasRange && "text-muted-foreground",
              className,
            )}
          >
            <Coins className="mr-2 h-4 w-4 shrink-0" />
            <span className="truncate">{label}</span>
          </Button>
        }
      />
      <PopoverContent className="w-64 space-y-3" align="start">
        <div className="space-y-1">
          <p className="text-sm font-medium">Amount ({currency})</p>
          <p className="text-xs text-muted-foreground">
            Matches income and expenses of this size.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 space-y-1">
            <Label htmlFor="amount-min" className="text-xs">
              From
            </Label>
            <Input
              id="amount-min"
              type="number"
              inputMode="decimal"
              min={0}
              step="0.01"
              placeholder="0"
              value={minAmount}
              onChange={(e) => onAmountChange("minAmount", e.target.value)}
            />
          </div>
          <div className="flex-1 space-y-1">
            <Label htmlFor="amount-max" className="text-xs">
              To
            </Label>
            <Input
              id="amount-max"
              type="number"
              inputMode="decimal"
              min={0}
              step="0.01"
              placeholder="Any"
              value={maxAmount}
              onChange={(e) => onAmountChange("maxAmount", e.target.value)}
            />
          </div>
        </div>
        {hasRange && (
          <Button
            variant="ghost"
            size="sm"
            className="w-full"
            onClick={() => {
              onAmountChange("minAmount", "");
              onAmountChange("maxAmount", "");
            }}
          >
            Clear
          </Button>
        )}
      </PopoverContent>
    </Popover>
  );
}
