import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import { format } from "date-fns";
import {
  CreditCard,
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
} from "lucide-react";
import { apiClient } from "../lib/api";
import StatCard from "../components/analytics/StatCard";
import BalanceChart from "../components/analytics/BalanceChart";
import TransactionDistribution from "../components/analytics/TransactionDistribution";
import MonthlyTrends from "../components/analytics/MonthlyTrends";
import { DateRangePicker } from "../components/filters/DateRangePicker";
import type { DatePreset } from "../components/filters/DateRangePicker";
import { AccountCombobox } from "../components/filters/AccountCombobox";
import { Card, CardContent } from "../components/ui/card";
import { TIME_PERIODS } from "../lib/timePeriods";

const analyticsPresets: DatePreset[] = TIME_PERIODS.map((p) => ({
  label: p.label,
  getValue: p.getDateRange,
}));

function AnalyticsDashboard() {
  // Default date range: last 365 days
  const defaultRange = TIME_PERIODS.find((p) => p.value === "365d")!.getDateRange();
  const [startDate, setStartDate] = useState(defaultRange.startDate);
  const [endDate, setEndDate] = useState(defaultRange.endDate);
  const [selectedAccount, setSelectedAccount] = useState("");

  const accountId = selectedAccount || undefined;

  const handleDateRangeChange = (start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
  };

  const subtitle = useMemo(() => {
    const from = new Date(startDate);
    const to = new Date(endDate);
    return `${format(from, "MMM d, yyyy")} – ${format(to, "MMM d, yyyy")}`;
  }, [startDate, endDate]);

  // Fetch analytics data
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["transaction-stats", startDate, endDate, accountId],
    queryFn: () => apiClient.getTransactionStats(startDate, endDate, accountId),
  });

  const { data: accounts, isLoading: accountsLoading } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => apiClient.getAccounts(),
  });

  const { data: balances, isLoading: balancesLoading } = useQuery({
    queryKey: ["historical-balances", startDate, endDate, accountId],
    queryFn: () =>
      apiClient.getHistoricalBalances(startDate, endDate, accountId),
  });

  const isLoading = statsLoading || accountsLoading || balancesLoading;

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="animate-pulse">
          <div className="h-8 bg-muted rounded w-48 mb-6"></div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-24 bg-muted rounded"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="h-96 bg-muted rounded"></div>
            <div className="h-96 bg-muted rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Filters */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <AccountCombobox
          accounts={accounts}
          selectedAccount={selectedAccount}
          onAccountChange={setSelectedAccount}
          className="w-[260px]"
        />
        <DateRangePicker
          startDate={startDate}
          endDate={endDate}
          onDateRangeChange={handleDateRangeChange}
          presets={analyticsPresets}
        />
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <StatCard
          title="Total Transactions"
          value={stats?.total_transactions || 0}
          subtitle={subtitle}
          icon={Activity}
          iconColor="blue"
        />
        <StatCard
          title="Total Income"
          value={`€${(stats?.total_income || 0).toLocaleString()}`}
          subtitle="Inflows this period"
          icon={TrendingUp}
          iconColor="green"
          shouldBlur={true}
        />
        <StatCard
          title="Total Expenses"
          value={`€${(stats?.total_expenses || 0).toLocaleString()}`}
          subtitle="Outflows this period"
          icon={TrendingDown}
          iconColor="red"
          shouldBlur={true}
        />
        <StatCard
          title="Net Change"
          value={`€${(stats?.net_change || 0).toLocaleString()}`}
          subtitle="Income minus expenses"
          icon={CreditCard}
          iconColor={(stats?.net_change || 0) >= 0 ? "green" : "red"}
          shouldBlur={true}
        />
        <StatCard
          title="Average Transaction"
          value={`€${Math.abs(stats?.average_transaction || 0).toLocaleString()}`}
          subtitle="Per transaction"
          icon={Activity}
          iconColor="purple"
          shouldBlur={true}
        />
        <StatCard
          title="Active Accounts"
          value={stats?.accounts_included || 0}
          subtitle="With recent activity"
          icon={Users}
          iconColor="orange"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardContent className="p-6">
            <BalanceChart data={balances || []} accounts={accounts || []} />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <TransactionDistribution accounts={accounts || []} />
          </CardContent>
        </Card>
      </div>

      {/* Monthly Trends */}
      <Card>
        <CardContent className="p-6">
          <MonthlyTrends
            dateFrom={startDate}
            dateTo={endDate}
            accountId={accountId}
          />
        </CardContent>
      </Card>
    </div>
  );
}

export const Route = createFileRoute("/analytics")({
  component: AnalyticsDashboard,
});
