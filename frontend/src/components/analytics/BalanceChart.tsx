import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";
import { cn, dominantCurrency, formatCurrency } from "../../lib/utils";
import { getAccountDisplayName } from "../../lib/accountDisplay";
import type { Balance, Account } from "../../types/api";

const CHART_COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
];

interface BalanceChartProps {
  data: Balance[];
  accounts: Account[];
  className?: string;
}

interface ChartDataPoint {
  date: string;
  balance: number;
  account_id: string;
}

interface AggregatedDataPoint {
  date: string;
  [key: string]: string | number;
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

export default function BalanceChart({
  data,
  accounts,
  className,
}: BalanceChartProps) {
  const { isBalanceVisible } = useBalanceVisibility();

  // Create a lookup map for account info
  const accountMap = accounts.reduce(
    (map, account) => {
      map[account.id] = account;
      return map;
    },
    {} as Record<string, Account>,
  );

  const displayName = (accountId: string): string => {
    const account = accountMap[accountId];
    return account
      ? getAccountDisplayName(account)
      : `Account ${accountId.split("-")[1]}`;
  };
  // Stacked areas only make sense in one currency — keep the dominant one
  const currency = dominantCurrency(data.map((balance) => balance.currency));

  // Process balance data for the chart
  // Backend already picks the best balance type per account, so no client-side type filtering needed
  const chartData = data
    .filter((balance) => (balance.currency || currency) === currency)
    .map((balance) => ({
      date: new Date(balance.reference_date).toLocaleDateString("en-GB"), // DD/MM/YYYY format
      balance: balance.balance_amount,
      account_id: balance.account_id,
    }))
    .sort(
      (a, b) =>
        new Date(a.date.split("/").reverse().join("/")).getTime() -
        new Date(b.date.split("/").reverse().join("/")).getTime(),
    );

  // Group by account and aggregate
  const accountBalances: { [key: string]: ChartDataPoint[] } = {};
  chartData.forEach((item) => {
    if (!accountBalances[item.account_id]) {
      accountBalances[item.account_id] = [];
    }
    accountBalances[item.account_id].push(item);
  });

  // Create aggregated data points
  const aggregatedData: { [key: string]: AggregatedDataPoint } = {};
  Object.entries(accountBalances).forEach(([accountId, balances]) => {
    balances.forEach((balance) => {
      if (!aggregatedData[balance.date]) {
        aggregatedData[balance.date] = { date: balance.date };
      }
      aggregatedData[balance.date][accountId] = balance.balance;
    });
  });

  const finalData = Object.values(aggregatedData).sort(
    (a, b) =>
      new Date(a.date.split("/").reverse().join("/")).getTime() -
      new Date(b.date.split("/").reverse().join("/")).getTime(),
  );

  const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card p-3 border rounded shadow-lg">
          <p className="font-medium text-foreground">Date: {label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {displayName(entry.name)}: {formatCurrency(entry.value, currency)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (finalData.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-4">
          Balance Progress
        </h3>
        <div className="h-80 flex items-center justify-center text-muted-foreground">
          No balance data available
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <h3 className="text-lg font-medium text-foreground mb-4">
        Balance Progress Over Time
      </h3>
      <div className={cn("h-80", !isBalanceVisible && "blur-md select-none")}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={finalData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
              tickFormatter={(value) => {
                // Convert DD/MM/YYYY back to a proper date for formatting
                const [day, month, year] = value.split("/");
                const date = new Date(year, month - 1, day);
                return date.toLocaleDateString("en-GB", {
                  month: "short",
                  day: "numeric",
                });
              }}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
              tickFormatter={(value) => formatCurrency(value, currency)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {Object.keys(accountBalances).map((accountId, index) => (
              <Area
                key={accountId}
                type="monotone"
                dataKey={accountId}
                stackId="1"
                fill={CHART_COLORS[index % CHART_COLORS.length]}
                stroke={CHART_COLORS[index % CHART_COLORS.length]}
                name={displayName(accountId)}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
