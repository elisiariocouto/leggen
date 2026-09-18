import { useQuery } from "@tanstack/react-query";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";
import { cn, formatCurrency } from "../../lib/utils";
import { Skeleton } from "../ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import Sparkline from "./Sparkline";
import apiClient from "../../lib/api";
import { queryKeys } from "../../lib/queryKeys";
import { isCompleteMonth, median, monthLabel } from "../../lib/months";
import type { CategoryMonthly } from "../../types/api";

/** A month this far off the category's typical month gets called out. */
const NOTABLE_CHANGE_PCT = 15;

/** Fewer complete months than this and "typical" is just noise. */
const MIN_MONTHS_FOR_TYPICAL = 3;

const compact = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

interface CategoryMatrixProps {
  className?: string;
  dateFrom: string;
  dateTo: string;
  accountId?: string;
  onSelectCategory?: (categoryId: number | null) => void;
}

/** Column heading: month name, plus the year on the first column and each January. */
function heading(month: string, index: number): string {
  return index === 0 || month.endsWith("-01")
    ? monthLabel(month)
    : monthLabel(month, "short");
}

/**
 * Cell shading relative to the row's own busiest month, so every category
 * shows its seasonality regardless of size. Mixed from the primary colour
 * so it follows the theme.
 */
function cellStyle(value: number, rowMax: number): React.CSSProperties {
  if (value <= 0 || rowMax <= 0) return {};
  const strength = Math.round(8 + 72 * (value / rowMax));
  return {
    backgroundColor: `color-mix(in oklch, var(--color-primary) ${strength}%, transparent)`,
  };
}

function isStrong(value: number, rowMax: number): boolean {
  return rowMax > 0 && value / rowMax > 0.55;
}

/**
 * Every category by every month: the table twin of the stacked chart. The
 * chart shows the shape of a year; this shows the numbers, including the
 * categories the chart folds into "Other". The last columns compare the
 * latest complete month with the category's typical month.
 */
export default function CategoryMatrix({
  className,
  dateFrom,
  dateTo,
  accountId,
  onSelectCategory,
}: CategoryMatrixProps) {
  const { isBalanceVisible } = useBalanceVisibility();

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.spendingByCategory(dateFrom, dateTo, accountId),
    queryFn: () =>
      apiClient.getSpendingByCategory({ dateFrom, dateTo, accountId }),
    placeholderData: (previousData) => previousData,
  });

  const title = (
    <h3 className="text-lg font-medium text-foreground">
      Category by month
    </h3>
  );

  if (isLoading) {
    return (
      <div className={className}>
        {title}
        <Skeleton className="h-64 w-full mt-4" />
      </div>
    );
  }

  if (!data || data.categories.length === 0) {
    return (
      <div className={className}>
        {title}
        <div className="h-40 flex items-center justify-center text-muted-foreground">
          No spending in this period
        </div>
      </div>
    );
  }

  const currency = data.currency ?? "EUR";
  const months = data.months;
  const complete = months.map((m) => isCompleteMonth(m, dateFrom, dateTo));
  // Compare the latest complete month, not a half-elapsed one, and never
  // against itself.
  const latestIndex = complete.lastIndexOf(true);
  const baselineIndexes = months
    .map((_, i) => i)
    .filter((i) => complete[i] && i !== latestIndex);
  const canCompare =
    latestIndex >= 0 && baselineIndexes.length >= MIN_MONTHS_FOR_TYPICAL;

  const typicalOf = (row: CategoryMonthly): number | null =>
    canCompare ? median(baselineIndexes.map((i) => row.monthly[i])) : null;

  const totals = months.map((_, i) =>
    data.categories.reduce((sum, c) => sum + c.monthly[i], 0),
  );
  const grandTotal = totals.reduce((sum, v) => sum + v, 0);
  const totalsTypical = canCompare
    ? median(baselineIndexes.map((i) => totals[i]))
    : null;

  const renderChange = (latest: number, typical: number | null) => {
    if (typical == null) return <span className="text-muted-foreground">–</span>;
    if (typical === 0) {
      return latest > 0 ? (
        <span className="text-negative font-medium">new</span>
      ) : (
        <span className="text-muted-foreground">–</span>
      );
    }
    const pct = ((latest - typical) / typical) * 100;
    const notable = Math.abs(pct) >= NOTABLE_CHANGE_PCT;
    return (
      <span
        className={cn(
          "tabular-nums",
          notable && pct > 0 && "text-negative font-medium",
          notable && pct < 0 && "text-positive font-medium",
          !notable && "text-muted-foreground",
        )}
        title={`${formatCurrency(latest, currency)} against a typical ${formatCurrency(typical, currency)}`}
      >
        {pct > 0 ? "+" : ""}
        {Math.abs(pct) >= 1000 ? ">999" : Math.round(pct)}%
      </span>
    );
  };

  return (
    <div className={className}>
      <div className="mb-4">
        {title}
        <p className="text-sm text-muted-foreground">
          Shading is relative to each category&apos;s own busiest month
          {canCompare && (
            <>
              {" · "}
              {monthLabel(months[latestIndex])} compared with the median of
              the other complete months
            </>
          )}
        </p>
      </div>
      <div
        className={cn(
          "overflow-x-auto -mx-6 px-6",
          !isBalanceVisible && "blur-md select-none",
        )}
      >
        <Table className="text-xs">
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="sticky left-0 bg-card min-w-[140px]">
                Category
              </TableHead>
              {months.map((m, i) => (
                <TableHead
                  key={m}
                  className={cn(
                    "text-right whitespace-nowrap",
                    !complete[i] && "italic",
                  )}
                  title={complete[i] ? undefined : "Partial month"}
                >
                  {heading(m, i)}
                </TableHead>
              ))}
              <TableHead className="text-right">Total</TableHead>
              <TableHead className="text-right">Typical</TableHead>
              <TableHead className="text-right">Trend</TableHead>
              <TableHead className="text-right whitespace-nowrap">
                {canCompare
                  ? `${monthLabel(months[latestIndex], "short")} vs typical`
                  : "vs typical"}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.categories.map((row) => {
              const uncategorized = row.category_id == null;
              const rowMax = Math.max(...row.monthly);
              const typical = typicalOf(row);
              return (
                <TableRow
                  key={row.category_id ?? "uncategorized"}
                  className={cn(
                    uncategorized && "text-muted-foreground",
                    onSelectCategory && "cursor-pointer",
                  )}
                  onClick={
                    onSelectCategory
                      ? () => onSelectCategory(row.category_id ?? null)
                      : undefined
                  }
                >
                  <TableCell className="sticky left-0 bg-card font-medium whitespace-nowrap">
                    <span className="flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 rounded-full shrink-0"
                        style={
                          uncategorized
                            ? {
                                backgroundImage:
                                  "repeating-linear-gradient(45deg, var(--color-muted-foreground) 0 1.5px, var(--color-muted) 1.5px 4px)",
                              }
                            : { backgroundColor: row.category_color }
                        }
                      />
                      {row.category_name}
                    </span>
                  </TableCell>
                  {row.monthly.map((value, i) => (
                    <TableCell
                      key={months[i]}
                      className={cn(
                        "text-right tabular-nums rounded-sm",
                        value <= 0 && "text-muted-foreground/60",
                        isStrong(value, rowMax) && "text-primary-foreground",
                      )}
                      style={cellStyle(value, rowMax)}
                      title={`${row.category_name} · ${monthLabel(months[i])} · ${formatCurrency(value, currency)}`}
                    >
                      {value > 0 ? compact.format(value) : "–"}
                    </TableCell>
                  ))}
                  <TableCell className="text-right tabular-nums font-medium text-foreground">
                    {formatCurrency(row.total, currency)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {typical == null ? "–" : formatCurrency(typical, currency)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Sparkline
                      values={row.monthly}
                      endColor={
                        uncategorized
                          ? "var(--color-muted-foreground)"
                          : row.category_color
                      }
                      className="inline-block align-middle"
                    />
                  </TableCell>
                  <TableCell className="text-right">
                    {canCompare
                      ? renderChange(row.monthly[latestIndex], typical)
                      : "–"}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
          <TableFooter>
            <TableRow className="hover:bg-transparent">
              <TableCell className="sticky left-0 bg-card">
                All spending
              </TableCell>
              {totals.map((value, i) => (
                <TableCell
                  key={months[i]}
                  className="text-right tabular-nums"
                >
                  {value > 0 ? compact.format(value) : "–"}
                </TableCell>
              ))}
              <TableCell className="text-right tabular-nums">
                {formatCurrency(grandTotal, currency)}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {totalsTypical == null
                  ? "–"
                  : formatCurrency(totalsTypical, currency)}
              </TableCell>
              <TableCell />
              <TableCell className="text-right">
                {canCompare
                  ? renderChange(totals[latestIndex], totalsTypical)
                  : "–"}
              </TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      </div>
    </div>
  );
}
