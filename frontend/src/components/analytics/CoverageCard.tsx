import { useQuery } from "@tanstack/react-query";
import { Tag } from "lucide-react";
import { formatCurrency } from "../../lib/utils";
import { Card, CardContent } from "../ui/card";
import { BlurredValue } from "../ui/blurred-value";
import { Skeleton } from "../ui/skeleton";
import apiClient from "../../lib/api";
import { queryKeys } from "../../lib/queryKeys";

interface CoverageCardProps {
  dateFrom: string;
  dateTo: string;
  accountId?: string;
}

/**
 * How much of the period's spending the categories explain. Every category
 * figure on the page is only as good as this number, so it sits with the
 * headline totals rather than in a footnote.
 */
export default function CoverageCard({
  dateFrom,
  dateTo,
  accountId,
}: CoverageCardProps) {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.spendingByCategory(dateFrom, dateTo, accountId),
    queryFn: () =>
      apiClient.getSpendingByCategory({ dateFrom, dateTo, accountId }),
    placeholderData: (previousData) => previousData,
  });

  const share = data?.categorized_share ?? 0;
  const pct = Math.round(share * 100);
  const unexplained =
    data?.categories.find((c) => c.category_id == null)?.total ?? 0;
  const currency = data?.currency ?? "EUR";

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-muted-foreground">
              Categorized
            </p>
            {isLoading ? (
              <Skeleton className="h-7 w-24 my-0.5" />
            ) : (
              <p className="text-xl font-bold text-foreground">
                {pct}%{" "}
                <span className="text-sm font-normal text-muted-foreground">
                  of spending
                </span>
              </p>
            )}
            <div
              className="mt-2 h-1.5 w-full rounded-full bg-primary/15"
              role="progressbar"
              aria-valuenow={pct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Share of spending with a category"
            >
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${pct}%` }}
              />
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              {isLoading ? (
                " "
              ) : unexplained > 0 ? (
                <>
                  <BlurredValue>
                    {formatCurrency(unexplained, currency)}
                  </BlurredValue>{" "}
                  without a category
                </>
              ) : (
                "Every expense has a category"
              )}
            </p>
          </div>
          <div className="ml-3 p-2 rounded-full bg-muted shrink-0">
            <Tag className="h-5 w-5 text-muted-foreground" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
