import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";
import { cn, formatCurrency } from "../../lib/utils";
import { Skeleton } from "../ui/skeleton";
import {
  CHART_AXIS_TICK,
  CHART_GRID_COLOR,
  EXPENSE_COLOR,
  INCOME_COLOR,
} from "../../lib/chartColors";
import apiClient from "../../lib/api";
import { queryKeys } from "../../lib/queryKeys";

interface MonthlyTrendsProps {
  className?: string;
  dateFrom: string;
  dateTo: string;
  accountId?: string;
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  label?: string;
}

export default function MonthlyTrends({
  className,
  dateFrom,
  dateTo,
  accountId,
}: MonthlyTrendsProps) {
  const { isBalanceVisible } = useBalanceVisibility();

  const { data: monthlyData, isLoading } = useQuery({
    queryKey: queryKeys.transactionStatsMonthly(dateFrom, dateTo, accountId),
    queryFn: () =>
      apiClient.getTransactionStatsByMonth(dateFrom, dateTo, accountId),
    placeholderData: (previousData) => previousData,
  });

  if (isLoading) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-4">
          Monthly Spending Trends
        </h3>
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (!monthlyData || monthlyData.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-4">
          Monthly Spending Trends
        </h3>
        <div className="h-80 flex items-center justify-center text-muted-foreground">
          No transaction data available
        </div>
      </div>
    );
  }

  const currency = monthlyData[0]?.currency ?? "EUR";

  const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card p-3 border rounded shadow-lg">
          <p className="font-medium text-foreground">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {formatCurrency(Math.abs(entry.value), currency)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className={className}>
      <h3 className="text-lg font-medium text-foreground mb-4">
        Monthly Spending Trends
      </h3>
      <div className={cn("h-80", !isBalanceVisible && "blur-md select-none")}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={monthlyData}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID_COLOR} />
            <XAxis
              dataKey="month"
              tick={CHART_AXIS_TICK}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis
              tick={CHART_AXIS_TICK}
              tickFormatter={(value) => formatCurrency(value, currency)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="income" fill={INCOME_COLOR} name="Income" />
            <Bar dataKey="expenses" fill={EXPENSE_COLOR} name="Expenses" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 flex justify-center space-x-6 text-sm text-foreground">
        <div className="flex items-center">
          <div
            className="w-3 h-3 rounded mr-2"
            style={{ backgroundColor: INCOME_COLOR }}
          />
          <span>Income</span>
        </div>
        <div className="flex items-center">
          <div
            className="w-3 h-3 rounded mr-2"
            style={{ backgroundColor: EXPENSE_COLOR }}
          />
          <span>Expenses</span>
        </div>
      </div>
    </div>
  );
}
