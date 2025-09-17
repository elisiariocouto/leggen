"use client"

import { TrendingUp } from "lucide-react"
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
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


export default function BalanceChart({
  data,
  accounts,
  className,
}: BalanceChartProps) {
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

  // Create chart config for shadcn charts
  const accountIds = Object.keys(accountBalances);
  const chartConfig: ChartConfig = accountIds.reduce((config, accountId, index) => {
    const colors = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)"];
    config[accountId] = {
      label: getAccountDisplayName(accountId),
      color: colors[index % colors.length],
    };
    return config;
  }, {} as ChartConfig);


  if (finalData.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-4">
          Balance Progress Over Time
        </h3>
        <div className="h-80 flex items-center justify-center text-muted-foreground">
          No balance data available
        </div>
      </div>
    );
  }

  // Calculate total balance for trending calculation
  const totalBalance = finalData[finalData.length - 1]
    ? Object.keys(accountBalances).reduce((total, accountId) => {
        const balance = finalData[finalData.length - 1][accountId] as number || 0;
        return total + balance;
      }, 0)
    : 0;

  const previousTotalBalance = finalData[finalData.length - 2]
    ? Object.keys(accountBalances).reduce((total, accountId) => {
        const balance = finalData[finalData.length - 2][accountId] as number || 0;
        return total + balance;
      }, 0)
    : totalBalance;

  const percentChange = previousTotalBalance !== 0
    ? ((totalBalance - previousTotalBalance) / previousTotalBalance * 100)
    : 0;

  return (
    <div className={className}>
      <div className="mb-4">
        <h3 className="text-lg font-medium text-foreground mb-1">
          Balance Progress Over Time
        </h3>
        <p className="text-sm text-muted-foreground">
          Account balances showing progression across all connected accounts
        </p>
      </div>
      <div className="h-80">
        <ChartContainer config={chartConfig}>
          <AreaChart
            accessibilityLayer
            data={finalData}
            margin={{
              left: -20,
              right: 12,
            }}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
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
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              tickCount={3}
              tickFormatter={(value) => `€${value.toLocaleString()}`}
            />
            <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
            {Object.keys(accountBalances).map((accountId) => (
              <Area
                key={accountId}
                dataKey={accountId}
                type="natural"
                fill={`var(--color-${accountId})`}
                fillOpacity={0.4}
                stroke={`var(--color-${accountId})`}
                stackId="a"
              />
            ))}
          </AreaChart>
        </ChartContainer>
      </div>
    </div>
  );
}
