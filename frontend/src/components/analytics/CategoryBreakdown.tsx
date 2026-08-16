import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";
import { cn, formatCurrency } from "../../lib/utils";
import { BlurredValue } from "../ui/blurred-value";
import { Skeleton } from "../ui/skeleton";
import { CHART_AXIS_TICK, CHART_GRID_COLOR } from "../../lib/chartColors";
import apiClient from "../../lib/api";
import type { CategoryStats } from "../../types/api";

interface CategoryBreakdownProps {
  className?: string;
  dateFrom: string;
  dateTo: string;
  accountId?: string;
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: CategoryStats;
    value: number;
  }>;
}

export default function CategoryBreakdown({
  className,
  dateFrom,
  dateTo,
  accountId,
}: CategoryBreakdownProps) {
  const { isBalanceVisible } = useBalanceVisibility();

  const { data: categoryData, isLoading } = useQuery({
    queryKey: ["category-stats", dateFrom, dateTo, accountId],
    queryFn: () => apiClient.getStatsByCategory(dateFrom, dateTo, accountId),
    placeholderData: (previousData) => previousData,
  });

  if (isLoading) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-4">
          Spending by Category
        </h3>
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  // Filter to categories with expenses and sort by expenses descending
  const chartData = (categoryData || [])
    .filter((cat) => cat.expenses > 0)
    .sort((a, b) => b.expenses - a.expenses);

  if (chartData.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-4">
          Spending by Category
        </h3>
        <div className="h-80 flex items-center justify-center text-muted-foreground">
          No categorized expense data available
        </div>
      </div>
    );
  }

  const totalExpenses = chartData.reduce((sum, cat) => sum + cat.expenses, 0);
  const currency = chartData[0]?.currency ?? "EUR";

  const CustomTooltip = ({ active, payload }: TooltipProps) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const percentage = ((data.expenses / totalExpenses) * 100).toFixed(1);
      return (
        <div className="bg-card p-3 border rounded shadow-lg">
          <p className="font-medium text-foreground">{data.category_name}</p>
          <p style={{ color: data.category_color }}>
            Expenses: {formatCurrency(data.expenses, currency)}
          </p>
          {data.income > 0 && (
            <p className="text-green-600 dark:text-green-400">
              Income: {formatCurrency(data.income, currency)}
            </p>
          )}
          <p className="text-muted-foreground">
            {percentage}% of total · {data.transaction_count} transactions
          </p>
        </div>
      );
    }
    return null;
  };

  // Calculate chart height based on number of categories (min 200, max 600)
  const chartHeight = Math.min(600, Math.max(200, chartData.length * 40 + 40));

  return (
    <div className={className}>
      <h3 className="text-lg font-medium text-foreground mb-4">
        Spending by Category
      </h3>
      <div
        className={cn(!isBalanceVisible && "blur-md select-none")}
        style={{ height: chartHeight }}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              horizontal={false}
              stroke={CHART_GRID_COLOR}
            />
            <XAxis
              type="number"
              tick={CHART_AXIS_TICK}
              tickFormatter={(value) => formatCurrency(value, currency)}
            />
            <YAxis
              type="category"
              dataKey="category_name"
              tick={CHART_AXIS_TICK}
              width={120}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="expenses" name="Expenses" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.category_color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 text-sm text-muted-foreground text-center">
        Total expenses:{" "}
        <span className="font-medium text-foreground">
          <BlurredValue>{formatCurrency(totalExpenses, currency)}</BlurredValue>
        </span>
        {" · "}
        {chartData.length} categories
      </div>
    </div>
  );
}
