import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";
import { cn, formatCurrency } from "../../lib/utils";
import { BlurredValue } from "../ui/blurred-value";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "../ui/sheet";
import { CHART_AXIS_TICK, CHART_GRID_COLOR } from "../../lib/chartColors";
import TopMerchants from "./TopMerchants";
import apiClient from "../../lib/api";
import { queryKeys } from "../../lib/queryKeys";
import { isCompleteMonth, median, monthLabel } from "../../lib/months";

/** Fewer complete months than this and "typical" is just noise. */
const MIN_MONTHS_FOR_TYPICAL = 3;

/**
 * The selected category: a real id, null for uncategorized spend, undefined
 * for nothing selected.
 */
export type SelectedCategory = number | null | undefined;

interface CategoryDetailProps {
  categoryId: SelectedCategory;
  onClose: () => void;
  dateFrom: string;
  dateTo: string;
  accountId?: string;
}

interface Point {
  month: string;
  value: number;
  complete: boolean;
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{ payload: Point }>;
  currency: string;
  typical: number | null;
}

// Module scope so the tooltip updates instead of remounting on every render.
function DetailTooltip({ active, payload, currency, typical }: TooltipProps) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="bg-card p-3 border rounded shadow-lg text-sm">
      <p className="font-medium text-foreground">
        {monthLabel(point.month)}
        {!point.complete && (
          <span className="text-muted-foreground font-normal"> · partial</span>
        )}
      </p>
      <p className="text-foreground tabular-nums">
        {formatCurrency(point.value, currency)}
      </p>
      {typical != null && typical > 0 && point.complete && (
        <p className="text-muted-foreground">
          {Math.round(((point.value - typical) / typical) * 100) > 0 ? "+" : ""}
          {Math.round(((point.value - typical) / typical) * 100)}% vs typical
        </p>
      )}
    </div>
  );
}

/**
 * One category on its own: its twelve months against its typical month,
 * and the merchants inside it. Opens from a segment of the stacked chart
 * or a row of the matrix; the numbers come from the same query, so it
 * opens instantly.
 */
export default function CategoryDetail({
  categoryId,
  onClose,
  dateFrom,
  dateTo,
  accountId,
}: CategoryDetailProps) {
  const { isBalanceVisible } = useBalanceVisibility();
  const open = categoryId !== undefined;

  const { data } = useQuery({
    queryKey: queryKeys.spendingByCategory(dateFrom, dateTo, accountId),
    queryFn: () =>
      apiClient.getSpendingByCategory({ dateFrom, dateTo, accountId }),
    enabled: open,
  });

  const row = open
    ? data?.categories.find((c) => (c.category_id ?? null) === categoryId)
    : undefined;
  const currency = data?.currency ?? "EUR";
  const uncategorized = categoryId === null;
  const filterId = uncategorized ? "uncategorized" : String(categoryId);

  const points: Point[] =
    data && row
      ? data.months.map((month, i) => ({
          month,
          value: row.monthly[i],
          complete: isCompleteMonth(month, dateFrom, dateTo),
        }))
      : [];
  const completePoints = points.filter((p) => p.complete);
  const latest = completePoints[completePoints.length - 1];
  const baseline = completePoints.slice(0, -1).map((p) => p.value);
  const typical =
    baseline.length >= MIN_MONTHS_FOR_TYPICAL ? median(baseline) : null;
  const color = uncategorized
    ? "var(--color-muted-foreground)"
    : (row?.category_color ?? "var(--color-muted-foreground)");

  return (
    <Sheet open={open} onOpenChange={(next) => !next && onClose()}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-xl overflow-y-auto"
      >
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <span
              className="h-3 w-3 rounded-full shrink-0"
              style={{ backgroundColor: color }}
            />
            {row?.category_name ?? "Category"}
          </SheetTitle>
          <SheetDescription>
            {row
              ? `${row.transaction_count} ${row.transaction_count === 1 ? "expense" : "expenses"} between ${monthLabel(data!.months[0])} and ${monthLabel(data!.months[data!.months.length - 1])}`
              : "Spending in this category over the selected period"}
          </SheetDescription>
        </SheetHeader>

        {row && data && (
          <div className="px-4 pb-6 space-y-6">
            <div className="flex flex-wrap gap-6">
              <div>
                <p className="text-xs text-muted-foreground">Total</p>
                <p className="text-xl font-semibold text-foreground">
                  <BlurredValue>{formatCurrency(row.total, currency)}</BlurredValue>
                </p>
              </div>
              {typical != null && (
                <div>
                  <p className="text-xs text-muted-foreground">Typical month</p>
                  <p className="text-xl font-semibold text-foreground">
                    <BlurredValue>{formatCurrency(typical, currency)}</BlurredValue>
                  </p>
                </div>
              )}
              {latest && typical != null && typical > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground">
                    {monthLabel(latest.month, "short")} vs typical
                  </p>
                  <p
                    className={cn(
                      "text-xl font-semibold tabular-nums",
                      latest.value > typical ? "text-negative" : "text-positive",
                    )}
                  >
                    {latest.value > typical ? "+" : ""}
                    {Math.round(((latest.value - typical) / typical) * 100)}%
                  </p>
                </div>
              )}
            </div>

            <div className={cn("h-48", !isBalanceVisible && "blur-md select-none")}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={points}
                  margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
                  barCategoryGap="30%"
                  // Otherwise the sheet's focus trap lands on the chart, which
                  // draws a focus ring and pins a tooltip to the first bar.
                  accessibilityLayer={false}
                >
                  <CartesianGrid stroke={CHART_GRID_COLOR} vertical={false} />
                  <XAxis
                    dataKey="month"
                    tick={CHART_AXIS_TICK}
                    tickFormatter={(month: string) => monthLabel(month, "short")}
                    tickLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={CHART_AXIS_TICK}
                    tickFormatter={(value: number) =>
                      formatCurrency(value, currency)
                    }
                    tickLine={false}
                    axisLine={false}
                    width={72}
                  />
                  <Tooltip
                    content={<DetailTooltip currency={currency} typical={typical} />}
                    cursor={{ fill: CHART_GRID_COLOR, fillOpacity: 0.3 }}
                  />
                  {typical != null && typical > 0 && (
                    <ReferenceLine
                      y={typical}
                      stroke="var(--color-foreground)"
                      strokeDasharray="3 4"
                      label={{
                        value: "typical",
                        position: "insideTopRight",
                        fill: "var(--color-muted-foreground)",
                        fontSize: 11,
                      }}
                    />
                  )}
                  <Bar
                    dataKey="value"
                    name={row.category_name}
                    isAnimationActive={false}
                    radius={[4, 4, 0, 0]}
                  >
                    {/* The latest complete month is the one being judged;
                        the rest are its context. */}
                    {points.map((point) => (
                      <Cell
                        key={point.month}
                        fill={color}
                        fillOpacity={
                          latest && point.month === latest.month ? 1 : 0.5
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <TopMerchants
              dateFrom={dateFrom}
              dateTo={dateTo}
              accountId={accountId}
              categoryId={filterId}
              limit={8}
              title="Merchants"
              subtitle="Compared with the preceding period of the same length"
            />

            <Link
              to="/"
              search={{
                category: filterId,
                from: dateFrom,
                to: dateTo,
                account: accountId,
              }}
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              View the transactions
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
