import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ArrowRight, WandSparkles } from "lucide-react";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";
import { cn, formatCurrency } from "../../lib/utils";
import { BlurredValue } from "../ui/blurred-value";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";
import apiClient from "../../lib/api";
import { queryKeys } from "../../lib/queryKeys";

const UNCATEGORIZED = "uncategorized";

interface NeedsRuleProps {
  className?: string;
  dateFrom: string;
  dateTo: string;
  accountId?: string;
  limit?: number;
}

/**
 * The largest merchants whose spend carries no category, biggest first.
 * Each row hands off to the rule editor with the merchant filled in, so
 * the list is worked down one rule at a time rather than one badge at a
 * time; the share figure says how much of the unexplained spend those
 * rows would clear.
 */
export default function NeedsRule({
  className,
  dateFrom,
  dateTo,
  accountId,
  limit = 8,
}: NeedsRuleProps) {
  const { isBalanceVisible } = useBalanceVisibility();

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.merchants(dateFrom, dateTo, accountId, UNCATEGORIZED),
    queryFn: () =>
      apiClient.getMerchants({
        dateFrom,
        dateTo,
        accountId,
        limit,
        categoryId: UNCATEGORIZED,
      }),
    placeholderData: (previousData) => previousData,
  });

  // The spending pivot already carries the uncategorized total, so the
  // coverage line costs no extra request.
  const { data: spending } = useQuery({
    queryKey: queryKeys.spendingByCategory(dateFrom, dateTo, accountId),
    queryFn: () =>
      apiClient.getSpendingByCategory({ dateFrom, dateTo, accountId }),
    placeholderData: (previousData) => previousData,
  });

  const title = (
    <h3 className="text-lg font-medium text-foreground">Needs a rule</h3>
  );

  if (isLoading) {
    return (
      <div className={className}>
        {title}
        <Skeleton className="h-80 w-full mt-4" />
      </div>
    );
  }

  const merchants = data?.merchants ?? [];
  if (merchants.length === 0) {
    return (
      <div className={className}>
        {title}
        <div className="h-40 flex items-center justify-center text-muted-foreground text-sm">
          Every expense in this period has a category.
        </div>
      </div>
    );
  }

  const currency = data?.currency ?? "EUR";
  const max = Math.max(...merchants.map((m) => m.total));
  const listed = merchants.reduce((sum, m) => sum + m.total, 0);
  const unexplained =
    spending?.categories.find((c) => c.category_id == null)?.total ?? 0;
  const coverage = unexplained > 0 ? Math.min(1, listed / unexplained) : null;

  return (
    <div className={className}>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div>
          {title}
          <p className="text-sm text-muted-foreground">
            Largest merchants without a category, so one rule clears the most
          </p>
        </div>
        <Link
          to="/"
          search={{
            category: UNCATEGORIZED,
            from: dateFrom,
            to: dateTo,
            account: accountId,
          }}
          className="text-sm text-primary hover:underline inline-flex items-center gap-1"
        >
          All uncategorized
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
      <div className={cn("space-y-1", !isBalanceVisible && "select-none")}>
        {merchants.map((merchant) => (
          <div key={merchant.merchant} className="relative">
            <div
              className="absolute inset-y-0 left-0 rounded bg-muted-foreground"
              style={{ width: `${(merchant.total / max) * 100}%`, opacity: 0.1 }}
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
              <span className="shrink-0 text-sm font-medium text-foreground tabular-nums">
                <BlurredValue>
                  {formatCurrency(merchant.total, currency)}
                </BlurredValue>
              </span>
              <Button
                variant="outline"
                size="sm"
                className="shrink-0 h-7"
                nativeButton={false}
                render={
                  <Link to="/rules" search={{ merchant: merchant.merchant }} />
                }
              >
                <WandSparkles className="h-3 w-3" />
                Write rule
              </Button>
            </div>
          </div>
        ))}
      </div>
      {coverage != null && (
        <p className="mt-4 text-xs text-muted-foreground text-center">
          These {merchants.length} merchants are {Math.round(coverage * 100)}%
          of the uncategorized spending in this period.
        </p>
      )}
    </div>
  );
}
