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
import { cn } from "../../lib/utils";
import type { Balance, Account } from "../../types/api";

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

  // Helper function to get bank name from institution_id
  const getBankName = (institutionId: string): string => {
    const bankMapping: Record<string, string> = {
      REVOLUT_REVOLT21: "Revolut",
      NUBANK_NUPBBR25: "Nu Pagamentos",
      BANCOBPI_BBPIPTPL: "Banco BPI",
      // Add more mappings as needed
    };
    return bankMapping[institutionId] || institutionId.split("_")[0];
  };

  // Helper function to create display name for account
  const getAccountDisplayName = (accountId: string): string => {
    const account = accountMap[accountId];
    if (account) {
      const bankName = getBankName(account.institution_id);
      const accountName = account.name || `Account ${accountId.split("-")[1]}`;
      return `${bankName} - ${accountName}`;
    }
    return `Account ${accountId.split("-")[1]}`;
  };
  // Process balance data for the chart
  const chartData = data
    .filter((balance) => balance.balance_type === "closingBooked")
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

  const colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"];

  const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card p-3 border rounded shadow-lg">
          <p className="font-medium text-foreground">Date: {label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {getAccountDisplayName(entry.name)}: €
              {entry.value.toLocaleString()}
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
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
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
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `€${value.toLocaleString()}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {Object.keys(accountBalances).map((accountId, index) => (
              <Area
                key={accountId}
                type="monotone"
                dataKey={accountId}
                stackId="1"
                fill={colors[index % colors.length]}
                stroke={colors[index % colors.length]}
                name={getAccountDisplayName(accountId)}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
