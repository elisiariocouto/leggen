import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Cell,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { format, parse } from "date-fns";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";
import { cn, formatCurrency } from "../../lib/utils";
import { Skeleton } from "../ui/skeleton";
import {
  CHART_AXIS_TICK,
  CHART_GRID_COLOR,
  EXPENSE_COLOR,
  INCOME_COLOR,
  NEUTRAL_LINE_COLOR,
} from "../../lib/chartColors";
import apiClient from "../../lib/api";
import { queryKeys } from "../../lib/queryKeys";
import type { CashFlowPoint } from "../../types/api";

interface CashFlowChartProps {
  className?: string;
  dateFrom: string;
  dateTo: string;
  accountId?: string;
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{ payload: CashFlowPoint }>;
  label?: string;
}

/** "2025-09" reads as "Sep 2025" on the axis and in the tooltip. */
function monthLabel(month: string): string {
  try {
    return format(parse(month, "yyyy-MM", new Date()), "MMM yyyy");
  } catch {
    return month;
  }
}

// Module scope: a component defined during render is a new type on every pass,
// which remounts the tooltip instead of updating it.
function CashFlowTooltip({
  active,
  payload,
  currency,
}: TooltipProps & { currency: string }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="bg-card p-3 border rounded shadow-lg">
      <p className="font-medium text-foreground">{monthLabel(point.month)}</p>
      <p className="text-positive">
        Income: {formatCurrency(point.income, currency)}
      </p>
      <p className="text-negative">
        Expenses: {formatCurrency(point.expenses, currency)}
      </p>
      <p className="text-foreground">
        Net: {formatCurrency(point.net, currency)}
      </p>
      <p className="text-muted-foreground">
        Running total: {formatCurrency(point.cumulative_net, currency)} ·{" "}
        {point.transaction_count} transactions
      </p>
    </div>
  );
}

/**
 * Monthly net, with the running total overlaid.
 *
 * Net per month is a polarity question — saved or overspent — so the bars are
 * signed and diverge from a zero baseline rather than stacking income against
 * expenses. Both series are money in the same currency, so the cumulative line
 * shares the one axis; a second scale would invent a correlation.
 */
export default function CashFlowChart({
  className,
  dateFrom,
  dateTo,
  accountId,
}: CashFlowChartProps) {
  const { isBalanceVisible } = useBalanceVisibility();

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.cashFlow(dateFrom, dateTo, accountId),
    queryFn: () => apiClient.getCashFlow({ dateFrom, dateTo, accountId }),
    placeholderData: (previousData) => previousData,
  });

  if (isLoading) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-1">Cash Flow</h3>
        <Skeleton className="h-80 w-full mt-4" />
      </div>
    );
  }

  const points = data?.points ?? [];
  if (points.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-1">Cash Flow</h3>
        <div className="h-80 flex items-center justify-center text-muted-foreground">
          No transactions in this period
        </div>
      </div>
    );
  }

  const currency = data?.currency ?? "EUR";
  const net = data?.net ?? 0;

  return (
    <div className={className}>
      <div className="mb-4">
        <h3 className="text-lg font-medium text-foreground">Cash Flow</h3>
        <p className="text-sm text-muted-foreground">
          {net >= 0 ? "Saved" : "Overspent"}{" "}
          <span
            className={cn(
              "font-medium",
              net >= 0 ? "text-positive" : "text-negative",
            )}
          >
            {formatCurrency(Math.abs(net), currency)}
          </span>{" "}
          over {points.length} {points.length === 1 ? "month" : "months"} ·{" "}
          {formatCurrency(data?.average_monthly_net ?? 0, currency)} in a typical
          month
        </p>
      </div>
      <div className={cn("h-80", !isBalanceVisible && "blur-md select-none")}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={points}
            margin={{ top: 8, right: 16, left: 8, bottom: 4 }}
          >
            <CartesianGrid stroke={CHART_GRID_COLOR} vertical={false} />
            <XAxis
              dataKey="month"
              tick={CHART_AXIS_TICK}
              tickFormatter={monthLabel}
              tickLine={false}
            />
            <YAxis
              tick={CHART_AXIS_TICK}
              tickFormatter={(value) => formatCurrency(value, currency)}
              tickLine={false}
              axisLine={false}
              width={80}
            />
            <Tooltip
              content={<CashFlowTooltip currency={currency} />}
              cursor={{ fill: CHART_GRID_COLOR, fillOpacity: 0.3 }}
            />
            <Bar dataKey="net" name="Net" radius={[4, 4, 0, 0]}>
              {points.map((point) => (
                <Cell
                  key={point.month}
                  fill={point.net >= 0 ? INCOME_COLOR : EXPENSE_COLOR}
                />
              ))}
            </Bar>
            <Line
              type="monotone"
              dataKey="cumulative_net"
              name="Running total"
              stroke={NEUTRAL_LINE_COLOR}
              strokeWidth={2}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 flex justify-center gap-6 text-sm text-muted-foreground">
        <span className="flex items-center gap-2">
          <span
            className="h-3 w-3 rounded-sm"
            style={{ backgroundColor: INCOME_COLOR }}
          />
          Surplus
        </span>
        <span className="flex items-center gap-2">
          <span
            className="h-3 w-3 rounded-sm"
            style={{ backgroundColor: EXPENSE_COLOR }}
          />
          Deficit
        </span>
        <span className="flex items-center gap-2">
          <span
            className="h-0.5 w-4"
            style={{ backgroundColor: NEUTRAL_LINE_COLOR }}
          />
          Running total
        </span>
      </div>
    </div>
  );
}
