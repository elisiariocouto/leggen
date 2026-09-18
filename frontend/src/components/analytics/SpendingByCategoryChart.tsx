import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";
import { cn, formatCurrency } from "../../lib/utils";
import { BlurredValue } from "../ui/blurred-value";
import { Skeleton } from "../ui/skeleton";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import { Tabs, TabsList, TabsTrigger } from "../ui/tabs";
import { CHART_AXIS_TICK, CHART_GRID_COLOR } from "../../lib/chartColors";
import apiClient from "../../lib/api";
import { queryKeys } from "../../lib/queryKeys";
import { isCompleteMonth, median, monthLabel } from "../../lib/months";
import type { SpendingByCategory } from "../../types/api";

/**
 * Categories drawn as their own segment. Past this many the palette stops
 * being tellable apart, so the tail folds into one "Other" segment and the
 * table below carries every category.
 */
const NAMED_SERIES = 6;
const OTHER_KEY = "other";
const UNCATEGORIZED_KEY = "uncategorized";
const NEUTRAL_COLOR = "var(--color-muted-foreground)";
const HATCH_ID = "spendingUncategorizedHatch";

type Mode = "amount" | "share";

interface Series {
  key: string;
  name: string;
  /** Solid colour for legend swatches and tooltip keys. */
  color: string;
  /** SVG fill for the bars; the uncategorized segment is a hatch pattern. */
  fill: string;
  /** A category id, null for uncategorized, undefined for the folded tail. */
  categoryId: number | null | undefined;
  monthly: number[];
  total: number;
}

interface Row {
  month: string;
  /** Amount total of the drawn series, whatever the mode. */
  total: number;
  amounts: Record<string, number>;
  [key: string]: number | string | Record<string, number>;
}

interface SpendingByCategoryChartProps {
  className?: string;
  dateFrom: string;
  dateTo: string;
  accountId?: string;
  /** Called with the segment's category (null for uncategorized) on click. */
  onSelectCategory?: (categoryId: number | null) => void;
}

function buildSeries(
  data: SpendingByCategory,
  includeUncategorized: boolean,
): Series[] {
  const categorized = data.categories.filter((c) => c.category_id != null);
  const named = categorized.slice(0, NAMED_SERIES);
  const tail = categorized.slice(NAMED_SERIES);
  const uncategorized = data.categories.find((c) => c.category_id == null);

  const series: Series[] = named.map((c) => ({
    key: `c${c.category_id}`,
    name: c.category_name,
    color: c.category_color,
    fill: c.category_color,
    categoryId: c.category_id,
    monthly: c.monthly,
    total: c.total,
  }));
  if (tail.length > 0) {
    series.push({
      key: OTHER_KEY,
      name: `Other (${tail.length} ${tail.length === 1 ? "category" : "categories"})`,
      color: NEUTRAL_COLOR,
      fill: NEUTRAL_COLOR,
      categoryId: undefined,
      monthly: data.months.map((_, i) =>
        tail.reduce((sum, c) => sum + c.monthly[i], 0),
      ),
      total: tail.reduce((sum, c) => sum + c.total, 0),
    });
  }
  if (uncategorized && includeUncategorized) {
    series.push({
      key: UNCATEGORIZED_KEY,
      name: "Uncategorized",
      color: NEUTRAL_COLOR,
      fill: `url(#${HATCH_ID})`,
      categoryId: null,
      monthly: uncategorized.monthly,
      total: uncategorized.total,
    });
  }
  return series;
}

function buildRows(months: string[], series: Series[], mode: Mode): Row[] {
  return months.map((month, i) => {
    const amounts: Record<string, number> = {};
    let total = 0;
    series.forEach((s) => {
      amounts[s.key] = s.monthly[i];
      total += s.monthly[i];
    });
    const row: Row = { month, total, amounts };
    series.forEach((s) => {
      row[s.key] =
        mode === "share"
          ? total > 0
            ? (amounts[s.key] / total) * 100
            : 0
          : amounts[s.key];
    });
    return row;
  });
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{ dataKey?: string | number; payload: Row }>;
  series: Series[];
  mode: Mode;
  currency: string;
}

// Module scope: a component created during render is a new type on every
// pass, which remounts the tooltip instead of updating it.
function SpendingTooltip({
  active,
  payload,
  series,
  mode,
  currency,
}: TooltipProps) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  // Top of the stack first, so the tooltip reads in the same order as the bar.
  const visible = [...series]
    .reverse()
    .filter((s) => (row.amounts[s.key] ?? 0) > 0);
  return (
    <div className="bg-card p-3 border rounded shadow-lg text-sm min-w-[200px]">
      <p className="font-medium text-foreground mb-1">
        {monthLabel(row.month)}
      </p>
      {visible.map((s) => {
        const amount = row.amounts[s.key];
        return (
          <div
            key={s.key}
            className="flex items-center justify-between gap-4 text-muted-foreground"
          >
            <span className="flex items-center gap-2">
              <span
                className="h-2.5 w-2.5 rounded-sm shrink-0"
                style={{ backgroundColor: s.color }}
              />
              {s.name}
            </span>
            <span className="text-foreground tabular-nums">
              {mode === "share" && row.total > 0
                ? `${Math.round((amount / row.total) * 100)}% · `
                : ""}
              {formatCurrency(amount, currency)}
            </span>
          </div>
        );
      })}
      <div className="flex items-center justify-between gap-4 border-t mt-2 pt-2 text-muted-foreground">
        <span>Total</span>
        <span className="text-foreground font-medium tabular-nums">
          {formatCurrency(row.total, currency)}
        </span>
      </div>
    </div>
  );
}

/**
 * One column per month, one segment per category: where the money goes,
 * and when. Categories carry their own colours, so the six largest are
 * drawn by name and the tail folds into a neutral "Other"; spend without a
 * category is hatched so it reads as unknown rather than as a category.
 */
export default function SpendingByCategoryChart({
  className,
  dateFrom,
  dateTo,
  accountId,
  onSelectCategory,
}: SpendingByCategoryChartProps) {
  const { isBalanceVisible } = useBalanceVisibility();
  const [mode, setMode] = useState<Mode>("amount");
  const [includeUncategorized, setIncludeUncategorized] = useState(true);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.spendingByCategory(dateFrom, dateTo, accountId),
    queryFn: () =>
      apiClient.getSpendingByCategory({ dateFrom, dateTo, accountId }),
    placeholderData: (previousData) => previousData,
  });

  const series = useMemo(
    () => (data ? buildSeries(data, includeUncategorized) : []),
    [data, includeUncategorized],
  );
  const rows = useMemo(
    () => (data ? buildRows(data.months, series, mode) : []),
    [data, series, mode],
  );

  const title = (
    <h3 className="text-lg font-medium text-foreground">Spending by month</h3>
  );

  if (isLoading) {
    return (
      <div className={className}>
        {title}
        <Skeleton className="h-80 w-full mt-4" />
      </div>
    );
  }

  if (!data || data.categories.length === 0) {
    return (
      <div className={className}>
        {title}
        <div className="h-80 flex items-center justify-center text-muted-foreground">
          No spending in this period
        </div>
      </div>
    );
  }

  const currency = data.currency ?? "EUR";
  const total = rows.reduce((sum, row) => sum + row.total, 0);
  // A partial first or last month would drag the median down.
  const typical = median(
    rows
      .filter((row) => isCompleteMonth(row.month, dateFrom, dateTo))
      .map((row) => row.total),
  );
  const categorizedPct = Math.round(data.categorized_share * 100);

  return (
    <div className={className}>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          {title}
          <p className="text-sm text-muted-foreground">
            <BlurredValue>{formatCurrency(total, currency)}</BlurredValue>{" "}
            over {rows.length} {rows.length === 1 ? "month" : "months"}
            {typical != null && (
              <>
                {" · "}
                <BlurredValue>{formatCurrency(typical, currency)}</BlurredValue>{" "}
                in a typical month
              </>
            )}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <Tabs value={mode} onValueChange={(value) => setMode(value as Mode)}>
            <TabsList>
              <TabsTrigger value="amount">Amount</TabsTrigger>
              <TabsTrigger value="share">Share</TabsTrigger>
            </TabsList>
          </Tabs>
          <div className="flex items-center gap-2">
            <Switch
              id="spending-include-uncategorized"
              checked={includeUncategorized}
              onCheckedChange={setIncludeUncategorized}
            />
            <Label
              htmlFor="spending-include-uncategorized"
              className="text-sm text-muted-foreground font-normal"
            >
              Uncategorized
            </Label>
          </div>
        </div>
      </div>

      <div className={cn("h-80", !isBalanceVisible && "blur-md select-none")}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={rows}
            margin={{ top: 8, right: 16, left: 8, bottom: 4 }}
            barCategoryGap="30%"
          >
            <defs>
              <pattern
                id={HATCH_ID}
                width="6"
                height="6"
                patternUnits="userSpaceOnUse"
                patternTransform="rotate(45)"
              >
                <rect width="6" height="6" fill="var(--color-muted)" />
                <line
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="6"
                  stroke={NEUTRAL_COLOR}
                  strokeWidth="2"
                />
              </pattern>
            </defs>
            <CartesianGrid stroke={CHART_GRID_COLOR} vertical={false} />
            <XAxis
              dataKey="month"
              tick={CHART_AXIS_TICK}
              tickFormatter={(month: string) => monthLabel(month, "short")}
              tickLine={false}
            />
            <YAxis
              tick={CHART_AXIS_TICK}
              tickFormatter={(value: number) =>
                mode === "share"
                  ? `${value}%`
                  : formatCurrency(value, currency)
              }
              domain={mode === "share" ? [0, 100] : undefined}
              tickLine={false}
              axisLine={false}
              width={mode === "share" ? 40 : 80}
            />
            <Tooltip
              content={
                <SpendingTooltip
                  series={series}
                  mode={mode}
                  currency={currency}
                />
              }
              cursor={{ fill: CHART_GRID_COLOR, fillOpacity: 0.3 }}
            />
            {series.map((s) => (
              <Bar
                key={s.key}
                dataKey={s.key}
                name={s.name}
                stackId="spend"
                fill={s.fill}
                isAnimationActive={false}
                cursor={
                  onSelectCategory && s.categoryId !== undefined
                    ? "pointer"
                    : undefined
                }
                onClick={() => {
                  if (onSelectCategory && s.categoryId !== undefined) {
                    onSelectCategory(s.categoryId);
                  }
                }}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex flex-wrap justify-center gap-x-5 gap-y-2 text-sm text-muted-foreground">
        {series.map((s) => (
          <span key={s.key} className="flex items-center gap-2">
            <span
              className="h-3 w-3 rounded-sm shrink-0"
              style={
                s.key === UNCATEGORIZED_KEY
                  ? {
                      backgroundImage: `repeating-linear-gradient(45deg, ${NEUTRAL_COLOR} 0 1.5px, var(--color-muted) 1.5px 4px)`,
                    }
                  : { backgroundColor: s.color }
              }
            />
            {s.name}
          </span>
        ))}
      </div>
      <p className="mt-3 text-xs text-muted-foreground text-center">
        {categorizedPct}% of this spending has a category.
      </p>
    </div>
  );
}
