import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import { BlurredValue } from "../ui/blurred-value";
import { dominantCurrency, formatCurrency } from "../../lib/utils";
import { getAccountDisplayName } from "../../lib/accountDisplay";
import type { Account } from "../../types/api";

const CHART_COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
];

interface TransactionDistributionProps {
  accounts: Account[];
  className?: string;
}

interface PieDataPoint {
  name: string;
  value: number;
  color: string;
  [key: string]: string | number;
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
  // A share-of-total pie only makes sense in one currency — keep accounts
  // whose primary balance is in the dominant one
  const currency = dominantCurrency(
    accounts.map(
      (account) => account.balances?.[0]?.currency || account.currency,
    ),
  );

  // Create pie chart data from account balances
  const pieData: PieDataPoint[] = accounts
    .filter(
      (account) =>
        (account.balances?.[0]?.currency || account.currency || currency) ===
        currency,
    )
    .map((account, index) => {
      const primaryBalance = account.balances?.[0]?.amount || 0;

      return {
        name: getAccountDisplayName(account),
        value: primaryBalance,
        color: CHART_COLORS[index % CHART_COLORS.length],
      };
    });

  const totalBalance = pieData.reduce((sum, item) => sum + item.value, 0);

  if (pieData.length === 0 || totalBalance === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-4">
          Account Distribution
        </h3>
        <div className="h-80 flex items-center justify-center text-muted-foreground">
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
        <div className="bg-card p-3 border rounded shadow-lg">
          <p className="font-medium text-foreground">{data.name}</p>
          <p className="text-primary">
            Balance:{" "}
            <BlurredValue>{formatCurrency(data.value, currency)}</BlurredValue>
          </p>
          <p className="text-muted-foreground">{percentage}% of total</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className={className}>
      <h3 className="text-lg font-medium text-foreground mb-4">
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
          <div
            key={index}
            className="flex items-center justify-between text-sm"
          >
            <div className="flex items-center">
              <div
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-foreground">{item.name}</span>
            </div>
            <span className="font-medium text-foreground">
              <BlurredValue>{formatCurrency(item.value, currency)}</BlurredValue>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
