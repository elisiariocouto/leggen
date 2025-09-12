import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import type { Account } from "../../types/api";

interface TransactionDistributionProps {
  accounts: Account[];
  className?: string;
}

interface PieDataPoint {
  name: string;
  value: number;
  color: string;
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: PieDataPoint;
  }>;
}

export default function TransactionDistribution({
  accounts,
  className,
}: TransactionDistributionProps) {
  // Create pie chart data from account balances
  const pieData: PieDataPoint[] = accounts.map((account, index) => {
    const closingBalance = account.balances.find(
      (balance) => balance.balance_type === "closingBooked"
    );
    
    const colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"];
    
    return {
      name: account.name || `Account ${account.id.split('-')[1]}`,
      value: closingBalance?.amount || 0,
      color: colors[index % colors.length],
    };
  });

  const totalBalance = pieData.reduce((sum, item) => sum + item.value, 0);

  if (pieData.length === 0 || totalBalance === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Account Distribution
        </h3>
        <div className="h-80 flex items-center justify-center text-gray-500">
          No account data available
        </div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }: TooltipProps) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const percentage = ((data.value / totalBalance) * 100).toFixed(1);
      return (
        <div className="bg-white p-3 border rounded shadow-lg">
          <p className="font-medium">{data.name}</p>
          <p className="text-blue-600">
            Balance: €{data.value.toLocaleString()}
          </p>
          <p className="text-gray-600">{percentage}% of total</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className={className}>
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        Account Balance Distribution
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              outerRadius={100}
              innerRadius={40}
              paddingAngle={2}
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              formatter={(value, entry: { color?: string }) => (
                <span style={{ color: entry.color }}>{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 grid grid-cols-1 gap-2">
        {pieData.map((item, index) => (
          <div key={index} className="flex items-center justify-between text-sm">
            <div className="flex items-center">
              <div
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-gray-700">{item.name}</span>
            </div>
            <span className="font-medium">€{item.value.toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}