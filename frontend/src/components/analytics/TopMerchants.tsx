import { useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowUp } from "lucide-react";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";
import { cn, formatCurrency } from "../../lib/utils";
import { BlurredValue } from "../ui/blurred-value";
import { Skeleton } from "../ui/skeleton";
import { chartColor } from "../../lib/chartColors";
import apiClient from "../../lib/api";
import { queryKeys } from "../../lib/queryKeys";

interface TopMerchantsProps {
  className?: string;
  dateFrom: string;
  dateTo: string;
  accountId?: string;
  limit?: number;
}

/**
 * Where the money goes, and what moved.
 *
 * Drawn as labelled rows rather than a bar chart: merchant names are long and
 * the reader wants the amount and its change, both of which a horizontal bar
 * chart pushes into a tooltip. The bar is a proportion cue behind the text.
 */
export default function TopMerchants({
  className,
  dateFrom,
  dateTo,
  accountId,
  limit = 10,
}: TopMerchantsProps) {
  const { isBalanceVisible } = useBalanceVisibility();

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.merchants(dateFrom, dateTo, accountId),
    queryFn: () =>
      apiClient.getMerchants({ dateFrom, dateTo, accountId, limit }),
    placeholderData: (previousData) => previousData,
  });

  if (isLoading) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-4">
          Top Merchants
        </h3>
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  const merchants = data?.merchants ?? [];
  if (merchants.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-4">
          Top Merchants
        </h3>
        <div className="h-80 flex items-center justify-center text-muted-foreground">
          No spending in this period
        </div>
      </div>
    );
  }

  const currency = data?.currency ?? "EUR";
  const max = Math.max(...merchants.map((m) => m.total));

  return (
    <div className={className}>
      <div className="mb-4">
        <h3 className="text-lg font-medium text-foreground">Top Merchants</h3>
        <p className="text-sm text-muted-foreground">
          Compared with the preceding period of the same length
        </p>
      </div>
      <div className={cn("space-y-2", !isBalanceVisible && "select-none")}>
        {merchants.map((merchant) => {
          const pct = merchant.change_pct;
          const isUp = pct != null && pct > 0;
          return (
            <div key={merchant.merchant} className="relative">
              {/* Proportion cue sits behind the row rather than beside it, so
                  long merchant names keep their full width. */}
              <div
                className="absolute inset-y-0 left-0 rounded"
                style={{
                  width: `${(merchant.total / max) * 100}%`,
                  backgroundColor: chartColor(0),
                  opacity: 0.12,
                }}
                aria-hidden="true"
              />
              <div className="relative flex items-center justify-between gap-3 px-3 py-2">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-foreground">
                    {merchant.merchant}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {merchant.transaction_count}{" "}
                    {merchant.transaction_count === 1
                      ? "transaction"
                      : "transactions"}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  {pct == null ? (
                    <span className="text-xs text-muted-foreground">New</span>
                  ) : (
                    <span
                      className={cn(
                        "flex items-center gap-0.5 text-xs",
                        isUp ? "text-negative" : "text-positive",
                      )}
                      // Spending more is the bad direction here, so the arrow
                      // carries the meaning and colour is not the only cue.
                      title={`${formatCurrency(merchant.previous_total, currency)} in the previous period`}
                    >
                      {isUp ? (
                        <ArrowUp className="h-3 w-3" />
                      ) : (
                        <ArrowDown className="h-3 w-3" />
                      )}
                      {/* Percentages off a tiny base run to four digits and
                          say nothing beyond "much more"; the exact previous
                          total is in the row's title. */}
                      {Math.abs(pct) >= 1000
                        ? ">999%"
                        : `${Math.round(Math.abs(pct))}%`}
                    </span>
                  )}
                  <span className="text-sm font-medium text-foreground tabular-nums">
                    <BlurredValue>
                      {formatCurrency(merchant.total, currency)}
                    </BlurredValue>
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {(data?.uncategorized_share ?? 0) > 0.5 && (
        <p className="mt-4 text-xs text-muted-foreground text-center">
          {Math.round((data?.uncategorized_share ?? 0) * 100)}% of these
          transactions are uncategorized — merchants are grouped from their
          descriptions.
        </p>
      )}
    </div>
  );
}
