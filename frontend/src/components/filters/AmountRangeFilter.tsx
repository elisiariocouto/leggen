import { Coins } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

/**
 * Filters by the direction of a transaction and by how large it is.
 *
 * Size ignores the sign: the app shows expenses as positive figures, so a
 * range of 40–50 is meant to catch a 45 payment and a 45 refund alike —
 * filtering on the signed value would instead exclude every expense from a
 * positive lower bound. Direction is the separate question of money in or
 * money out, and lives in the same popover because both describe the amount.
 */
const BOTH = "all";

const KIND_LABEL: Record<string, string> = {
  income: "Income",
  expense: "Expenses",
};

export interface AmountRangeFilterProps {
  minAmount: string;
  maxAmount: string;
  /** "income", "expense" or "" for both. */
  selectedKind: string;
  onAmountChange: (key: "minAmount" | "maxAmount", value: string) => void;
  onKindChange: (kind: string) => void;
  currency?: string;
  className?: string;
}

export function AmountRangeFilter({
  minAmount,
  maxAmount,
  selectedKind,
  onAmountChange,
  onKindChange,
  currency = "EUR",
  className,
}: AmountRangeFilterProps) {
  const hasRange = Boolean(minAmount || maxAmount);
  const hasKind = Boolean(selectedKind);
  const isActive = hasRange || hasKind;

  const rangeLabel = `${minAmount || "0"} – ${maxAmount || "∞"}`;
  const label = [hasKind && KIND_LABEL[selectedKind], hasRange && rangeLabel]
    .filter(Boolean)
    .join(" · ");

  return (
    <Popover>
      <PopoverTrigger
        render={
          <Button
            variant="outline"
            className={cn(
              "justify-start font-normal",
              !isActive && "text-muted-foreground",
              className,
            )}
          >
            <Coins className="mr-2 h-4 w-4 shrink-0" />
            <span className="truncate">{label || "Amount"}</span>
          </Button>
        }
      />
      <PopoverContent className="w-64 space-y-3" align="start">
        <Tabs
          value={selectedKind || BOTH}
          onValueChange={(value) => onKindChange(value === BOTH ? "" : value)}
        >
          <TabsList className="w-full">
            <TabsTrigger value={BOTH} className="flex-1">
              All
            </TabsTrigger>
            <TabsTrigger value="income" className="flex-1">
              Income
            </TabsTrigger>
            <TabsTrigger value="expense" className="flex-1">
              Expenses
            </TabsTrigger>
          </TabsList>
        </Tabs>
        <div className="space-y-1">
          <p className="text-sm font-medium">Size ({currency})</p>
          <p className="text-xs text-muted-foreground">
            Ignores the sign, so it matches a payment and a refund alike.
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
        {isActive && (
          <Button
            variant="ghost"
            size="sm"
            className="w-full"
            onClick={() => {
              onKindChange("");
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
