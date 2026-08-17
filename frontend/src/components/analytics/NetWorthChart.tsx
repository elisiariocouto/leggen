import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { format, parseISO } from "date-fns";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";
import { cn, formatCurrency } from "../../lib/utils";
import { Skeleton } from "../ui/skeleton";
import {
  CHART_AXIS_TICK,
  CHART_GRID_COLOR,
  chartColor,
} from "../../lib/chartColors";
import apiClient from "../../lib/api";
import { queryKeys } from "../../lib/queryKeys";
import type { NetWorthPoint } from "../../types/api";

interface NetWorthChartProps {
  className?: string;
  dateFrom: string;
  dateTo: string;
  accountId?: string;
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{ payload: NetWorthPoint }>;
}

function dayLabel(date: string): string {
  try {
    return format(parseISO(date), "d MMM yyyy");
  } catch {
    return date;
  }
}

// Module scope: see CashFlowChart.
function NetWorthTooltip({
  active,
  payload,
  currency,
}: TooltipProps & { currency: string }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  const accounts = Object.entries(point.accounts ?? {});
  return (
    <div className="bg-card p-3 border rounded shadow-lg">
      <p className="font-medium text-foreground">{dayLabel(point.date)}</p>
      <p className="text-foreground">
        Total: {formatCurrency(point.total, currency)}
      </p>
      {accounts.length > 1 && (
        <div className="mt-1 pt-1 border-t text-sm text-muted-foreground">
          {accounts.map(([name, amount]) => (
            <p key={name}>
              {name}: {formatCurrency(amount, currency)}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Total balance over time, from the snapshots sync records.
 *
 * One line rather than a stack per account: the question is "what do I have",
 * and a stacked area renders nonsensically as soon as one account is negative.
 * The per-account split lives in the tooltip instead.
 */
export default function NetWorthChart({
  className,
  dateFrom,
  dateTo,
  accountId,
}: NetWorthChartProps) {
  const { isBalanceVisible } = useBalanceVisibility();

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.netWorth(dateFrom, dateTo, accountId),
    queryFn: () => apiClient.getNetWorth({ dateFrom, dateTo, accountId }),
    placeholderData: (previousData) => previousData,
  });

  if (isLoading) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-1">Net Worth</h3>
        <Skeleton className="h-80 w-full mt-4" />
      </div>
    );
  }

  const points = data?.points ?? [];
  if (points.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-1">Net Worth</h3>
        <div className="h-80 flex flex-col items-center justify-center gap-1 text-muted-foreground">
          <p>No balance snapshots in this period</p>
          <p className="text-sm">
            Balances are recorded on each sync, so history starts at your first
            sync.
          </p>
        </div>
      </div>
    );
  }

  const currency = data?.currency ?? "EUR";
  const change = data?.change ?? 0;
  const changePct = data?.change_pct;

  return (
    <div className={className}>
      <div className="mb-4">
        <h3 className="text-lg font-medium text-foreground">Net Worth</h3>
        <p className="text-sm text-muted-foreground">
          <span
            className={cn(
              "font-medium",
              change >= 0 ? "text-positive" : "text-negative",
            )}
          >
            {change >= 0 ? "+" : "−"}
            {formatCurrency(Math.abs(change), currency)}
            {changePct != null && ` (${changePct > 0 ? "+" : ""}${changePct}%)`}
          </span>{" "}
          over this period
        </p>
      </div>
      <div className={cn("h-80", !isBalanceVisible && "blur-md select-none")}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={points}
            margin={{ top: 8, right: 16, left: 8, bottom: 4 }}
          >
            <defs>
              <linearGradient id="netWorthFill" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="0%"
                  stopColor={chartColor(0)}
                  stopOpacity={0.25}
                />
                <stop
                  offset="100%"
                  stopColor={chartColor(0)}
                  stopOpacity={0.02}
                />
              </linearGradient>
            </defs>
            <CartesianGrid stroke={CHART_GRID_COLOR} vertical={false} />
            <XAxis
              dataKey="date"
              tick={CHART_AXIS_TICK}
              tickLine={false}
              minTickGap={40}
              tickFormatter={(value) => {
                try {
                  return format(parseISO(value), "d MMM");
                } catch {
                  return value;
                }
              }}
            />
            <YAxis
              tick={CHART_AXIS_TICK}
              tickFormatter={(value) => formatCurrency(value, currency)}
              tickLine={false}
              axisLine={false}
              width={80}
              // Pad around the actual range rather than anchoring at zero: a
              // single payday spike would otherwise flatten the rest of the
              // year against the axis.
              domain={[
                (min: number) => Math.min(0, min - Math.abs(min) * 0.08),
                (max: number) => max + Math.abs(max) * 0.08,
              ]}
            />
            <Tooltip content={<NetWorthTooltip currency={currency} />} />
            <Area
              type="monotone"
              dataKey="total"
              name="Net worth"
              stroke={chartColor(0)}
              strokeWidth={2}
              fill="url(#netWorthFill)"
              dot={false}
              activeDot={{ r: 4 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-4 text-sm text-muted-foreground text-center">
        Recorded at each sync, so the line follows how often you sync.
      </p>
    </div>
  );
}
