import { useQuery } from "@tanstack/react-query";
import { format, parseISO } from "date-fns";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";
import { cn, formatCurrency } from "../../lib/utils";
import { BlurredValue } from "../ui/blurred-value";
import { Skeleton } from "../ui/skeleton";
import apiClient from "../../lib/api";
import { queryKeys } from "../../lib/queryKeys";
import type { RecurringPayment } from "../../types/api";

interface RecurringPaymentsProps {
  className?: string;
  dateFrom: string;
  dateTo: string;
  accountId?: string;
}

/** Roughly what one commitment costs per year, for the summary line. */
const PER_YEAR: Record<string, number> = {
  weekly: 52,
  biweekly: 26,
  monthly: 12,
  quarterly: 4,
  yearly: 1,
};

function annualized(payment: RecurringPayment): number {
  return payment.typical_amount * (PER_YEAR[payment.cadence] ?? 0);
}

function shortDate(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return format(parseISO(value), "d MMM");
  } catch {
    return value;
  }
}

/**
 * What the money is committed to.
 *
 * A table rather than a chart: each row carries a name, a cadence, an amount
 * and two dates, and the reader compares them by reading rather than by
 * relative size. Showing the evidence also makes a mis-grouped merchant
 * visible instead of hiding it inside a total.
 */
export default function RecurringPayments({
  className,
  dateFrom,
  dateTo,
  accountId,
}: RecurringPaymentsProps) {
  const { isBalanceVisible } = useBalanceVisibility();

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.recurring(dateFrom, dateTo, accountId),
    queryFn: () => apiClient.getRecurring({ dateFrom, dateTo, accountId }),
    placeholderData: (previousData) => previousData,
  });

  if (isLoading) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-4">Recurring</h3>
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  const payments = data ?? [];
  if (payments.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-4">Recurring</h3>
        <div className="h-80 flex flex-col items-center justify-center gap-1 text-muted-foreground">
          <p>No recurring payments detected</p>
          <p className="text-sm">
            A charge needs at least three regularly spaced occurrences.
          </p>
        </div>
      </div>
    );
  }

  const currency = payments[0]?.currency ?? "EUR";
  const yearlyTotal = payments.reduce((sum, p) => sum + annualized(p), 0);

  return (
    <div className={className}>
      <div className="mb-4">
        <h3 className="text-lg font-medium text-foreground">Recurring</h3>
        <p className="text-sm text-muted-foreground">
          {payments.length} detected ·{" "}
          <BlurredValue>{formatCurrency(yearlyTotal, currency)}</BlurredValue> a
          year at current prices
        </p>
      </div>
      <div className={cn("overflow-x-auto", !isBalanceVisible && "select-none")}>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-xs text-muted-foreground">
              <th className="pb-2 font-medium">Merchant</th>
              <th className="pb-2 font-medium">Every</th>
              <th className="pb-2 font-medium text-right">Amount</th>
              <th className="pb-2 font-medium text-right">Last</th>
              <th className="pb-2 font-medium text-right">Next</th>
            </tr>
          </thead>
          <tbody>
            {payments.map((payment) => (
              <tr
                key={`${payment.merchant}-${payment.typical_amount}`}
                className="border-b last:border-0"
              >
                <td className="py-2 pr-3">
                  <span className="block max-w-[16rem] truncate text-foreground">
                    {payment.merchant}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {payment.occurrences} charges
                  </span>
                </td>
                <td className="py-2 pr-3 text-muted-foreground">
                  {payment.cadence}
                </td>
                <td className="py-2 pr-3 text-right font-medium text-foreground tabular-nums">
                  <BlurredValue>
                    {formatCurrency(payment.typical_amount, currency)}
                  </BlurredValue>
                </td>
                <td className="py-2 pr-3 text-right text-muted-foreground tabular-nums">
                  {shortDate(payment.last_seen)}
                </td>
                <td className="py-2 text-right text-muted-foreground tabular-nums">
                  {shortDate(payment.next_expected)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-4 text-xs text-muted-foreground text-center">
        Detected from spending patterns, so an unusual description may be missed
        or grouped wrongly.
      </p>
    </div>
  );
}
