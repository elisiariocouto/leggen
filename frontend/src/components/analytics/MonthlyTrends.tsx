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
import apiClient from "../../lib/api";

interface MonthlyTrendsProps {
  className?: string;
  days?: number;
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
  days = 365,
}: MonthlyTrendsProps) {
  // Get pre-calculated monthly stats from the new endpoint
  const { data: monthlyData, isLoading } = useQuery({
    queryKey: ["monthly-stats", days],
    queryFn: async () => {
      return await apiClient.getMonthlyTransactionStats(days);
    },
  });

  // Calculate number of months to display based on days filter
  const getMonthsToDisplay = (days: number): number => {
    if (days <= 30) return 1;
    if (days <= 180) return 6;
    if (days <= 365) return 12;
    return Math.ceil(days / 30);
  };

  const monthsToDisplay = getMonthsToDisplay(days);
  const displayData = monthlyData ? monthlyData.slice(-monthsToDisplay) : [];

  if (isLoading) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-4">
          Monthly Spending Trends
        </h3>
        <div className="h-80 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (displayData.length === 0) {
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

  const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card p-3 border rounded shadow-lg">
          <p className="font-medium text-foreground">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: €{Math.abs(entry.value).toLocaleString()}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Generate dynamic title based on time period
  const getTitle = (days: number): string => {
    if (days <= 30) return "Monthly Spending Trends (Last 30 Days)";
    if (days <= 180) return "Monthly Spending Trends (Last 6 Months)";
    if (days <= 365) return "Monthly Spending Trends (Last 12 Months)";
    return `Monthly Spending Trends (Last ${Math.ceil(days / 30)} Months)`;
  };

  return (
    <div className={className}>
      <h3 className="text-lg font-medium text-foreground mb-4">
        {getTitle(days)}
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={displayData}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `€${value.toLocaleString()}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="income" fill="#10B981" name="Income" />
            <Bar dataKey="expenses" fill="#EF4444" name="Expenses" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 flex justify-center space-x-6 text-sm text-foreground">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-green-500 rounded mr-2" />
          <span>Income</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-red-500 rounded mr-2" />
          <span>Expenses</span>
        </div>
      </div>
    </div>
  );
}
