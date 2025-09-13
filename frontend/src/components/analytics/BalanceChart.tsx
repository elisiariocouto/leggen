import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
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

export default function BalanceChart({ data, accounts, className }: BalanceChartProps) {
  // Create a lookup map for account info
  const accountMap = accounts.reduce((map, account) => {
    map[account.id] = account;
    return map;
  }, {} as Record<string, Account>);

  // Helper function to get bank name from institution_id
  const getBankName = (institutionId: string): string => {
    const bankMapping: Record<string, string> = {
      'REVOLUT_REVOLT21': 'Revolut',
      'NUBANK_NUPBBR25': 'Nu Pagamentos',
      'BANCOBPI_BBPIPTPL': 'Banco BPI',
      // Add more mappings as needed
    };
    return bankMapping[institutionId] || institutionId.split('_')[0];
  };

  // Helper function to create display name for account
  const getAccountDisplayName = (accountId: string): string => {
    const account = accountMap[accountId];
    if (account) {
      const bankName = getBankName(account.institution_id);
      const accountName = account.name || `Account ${accountId.split('-')[1]}`;
      return `${bankName} - ${accountName}`;
    }
    return `Account ${accountId.split('-')[1]}`;
  };
  // Process balance data for the chart
  const chartData = data
    .filter((balance) => balance.balance_type === "closingBooked")
    .map((balance) => ({
      date: new Date(balance.reference_date).toLocaleDateString('en-GB'), // DD/MM/YYYY format
      balance: balance.balance_amount,
      account_id: balance.account_id,
    }))
    .sort((a, b) => new Date(a.date.split('/').reverse().join('/')).getTime() - new Date(b.date.split('/').reverse().join('/')).getTime());

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
    (a, b) => new Date(a.date.split('/').reverse().join('/')).getTime() - new Date(b.date.split('/').reverse().join('/')).getTime()
  );

  const colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"];

  if (finalData.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Balance Progress
        </h3>
        <div className="h-80 flex items-center justify-center text-gray-500">
          No balance data available
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        Balance Progress Over Time
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={finalData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => {
                // Convert DD/MM/YYYY back to a proper date for formatting
                const [day, month, year] = value.split('/');
                const date = new Date(year, month - 1, day);
                return date.toLocaleDateString('en-GB', {
                  month: "short",
                  day: "numeric",
                });
              }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `€${value.toLocaleString()}`}
            />
            <Tooltip
              formatter={(value: number) => [
                `€${value.toLocaleString()}`,
                "Balance",
              ]}
              labelFormatter={(label) => `Date: ${label}`}
            />
            <Legend />
            {Object.keys(accountBalances).map((accountId, index) => (
              <Line
                key={accountId}
                type="monotone"
                dataKey={accountId}
                stroke={colors[index % colors.length]}
                strokeWidth={2}
                dot={{ r: 4 }}
                name={getAccountDisplayName(accountId)}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}