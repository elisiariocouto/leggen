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

interface MonthlyData {
  month: string;
  income: number;
  expenses: number;
  net: number;
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

export default function MonthlyTrends({ className, days = 365 }: MonthlyTrendsProps) {
  // Get transactions for the specified period using analytics endpoint
  const { data: transactions, isLoading } = useQuery({
    queryKey: ["transactions", "monthly-trends", days],
    queryFn: async () => {
      return await apiClient.getTransactionsForAnalytics(days);
    },
  });

  // Process transactions into monthly data
  const monthlyData: MonthlyData[] = [];
  
  if (transactions) {
    const monthlyMap: { [key: string]: MonthlyData } = {};
    
    transactions.forEach((transaction) => {
      const date = new Date(transaction.transaction_date);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      
      if (!monthlyMap[monthKey]) {
        monthlyMap[monthKey] = {
          month: date.toLocaleDateString(undefined, { 
            year: 'numeric', 
            month: 'short' 
          }),
          income: 0,
          expenses: 0,
          net: 0,
        };
      }
      
      if (transaction.transaction_value > 0) {
        monthlyMap[monthKey].income += transaction.transaction_value;
      } else {
        monthlyMap[monthKey].expenses += Math.abs(transaction.transaction_value);
      }
      
      monthlyMap[monthKey].net = monthlyMap[monthKey].income - monthlyMap[monthKey].expenses;
    });
    
    // Convert to array and sort by date
    monthlyData.push(
      ...Object.entries(monthlyMap)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([, data]) => data)
        .slice(-12) // Last 12 months
    );
  }

  if (isLoading) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Monthly Spending Trends
        </h3>
        <div className="h-80 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (monthlyData.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Monthly Spending Trends
        </h3>
        <div className="h-80 flex items-center justify-center text-gray-500">
          No transaction data available
        </div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border rounded shadow-lg">
          <p className="font-medium">{label}</p>
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

  return (
    <div className={className}>
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        Monthly Spending Trends (Last 12 Months)
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={monthlyData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
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
      <div className="mt-4 flex justify-center space-x-6 text-sm">
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