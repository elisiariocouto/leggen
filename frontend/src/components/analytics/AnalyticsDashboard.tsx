import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { format } from "date-fns";
import {
  CreditCard,
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
} from "lucide-react";
import { apiClient } from "../../lib/api";
import { formatCurrency } from "../../lib/utils";
import StatCard from "./StatCard";
import BalanceChart from "./BalanceChart";
import TransactionDistribution from "./TransactionDistribution";
import MonthlyTrends from "./MonthlyTrends";
import CategoryBreakdown from "./CategoryBreakdown";
import { DateRangePicker } from "../filters/DateRangePicker";
import type { DatePreset } from "../filters/DateRangePicker";
import { AccountCombobox } from "../filters/AccountCombobox";
import { Card, CardContent } from "../ui/card";
import { queryKeys } from "../../lib/queryKeys";
import { TIME_PERIODS } from "../../lib/timePeriods";
import type { AnalyticsSearch } from "../../routes/analytics";

const analyticsPresets: DatePreset[] = TIME_PERIODS.map((p) => ({
  label: p.label,
  getValue: p.getDateRange,
}));

export default function AnalyticsDashboard() {
  // Filters live in the URL so a view can be bookmarked and shared.
  const search = useSearch({ from: "/analytics" });
  const navigate = useNavigate({ from: "/analytics" });

  // Absent params mean the default window, resolved on each render so a
  // saved link stays relative to today rather than freezing a past year.
  const defaultRange = useMemo(
    () => TIME_PERIODS.find((p) => p.value === "365d")!.getDateRange(),
    [],
  );
  const startDate = search.from ?? defaultRange.startDate;
  const endDate = search.to ?? defaultRange.endDate;
  const selectedAccount = search.account ?? "";

  const accountId = selectedAccount || undefined;

  const handleDateRangeChange = (start: string, end: string) => {
    navigate({
      search: (prev: AnalyticsSearch) => ({ ...prev, from: start, to: end }),
    });
  };

  const handleAccountChange = (nextAccount: string) => {
    navigate({
      search: (prev: AnalyticsSearch) => ({
        ...prev,
        account: nextAccount || undefined,
      }),
    });
  };

  const subtitle = useMemo(() => {
    const from = new Date(startDate);
    const to = new Date(endDate);
    return `${format(from, "MMM d, yyyy")} – ${format(to, "MMM d, yyyy")}`;
  }, [startDate, endDate]);

  // Fetch analytics data; placeholderData keeps the previous results visible
  // while a filter change refetches, instead of flashing the loading state
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: queryKeys.transactionStatsSummary(startDate, endDate, accountId),
    queryFn: () => apiClient.getTransactionStats(startDate, endDate, accountId),
    placeholderData: (previousData) => previousData,
  });

  const { data: accounts } = useQuery({
    queryKey: queryKeys.accounts,
    queryFn: () => apiClient.getAccounts(),
  });

  const { data: balances } = useQuery({
    queryKey: queryKeys.historicalBalances(startDate, endDate, accountId),
    queryFn: () =>
      apiClient.getHistoricalBalances(startDate, endDate, accountId),
    placeholderData: (previousData) => previousData,
  });

  const statsCurrency = stats?.currency ?? "EUR";

  return (
    <div className="space-y-8">
      {/* Filters */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <AccountCombobox
          accounts={accounts}
          selectedAccount={selectedAccount}
          onAccountChange={handleAccountChange}
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
          isLoading={statsLoading}
          title="Total Transactions"
          value={stats?.total_transactions || 0}
          subtitle={subtitle}
          icon={Activity}
          iconColor="blue"
        />
        <StatCard
          isLoading={statsLoading}
          title="Total Income"
          value={formatCurrency(stats?.total_income || 0, statsCurrency)}
          subtitle="Inflows this period"
          icon={TrendingUp}
          iconColor="green"
          shouldBlur={true}
        />
        <StatCard
          isLoading={statsLoading}
          title="Total Expenses"
          value={formatCurrency(stats?.total_expenses || 0, statsCurrency)}
          subtitle="Outflows this period"
          icon={TrendingDown}
          iconColor="red"
          shouldBlur={true}
        />
        <StatCard
          isLoading={statsLoading}
          title="Net Change"
          value={formatCurrency(stats?.net_change || 0, statsCurrency)}
          subtitle="Income minus expenses"
          icon={CreditCard}
          iconColor={(stats?.net_change || 0) >= 0 ? "green" : "red"}
          shouldBlur={true}
        />
        <StatCard
          isLoading={statsLoading}
          title="Average Transaction"
          value={formatCurrency(
            Math.abs(stats?.average_transaction || 0),
            statsCurrency,
          )}
          subtitle="Per transaction"
          icon={Activity}
          iconColor="purple"
          shouldBlur={true}
        />
        <StatCard
          isLoading={statsLoading}
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

      {/* Category Breakdown & Monthly Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardContent className="p-6">
            <CategoryBreakdown
              dateFrom={startDate}
              dateTo={endDate}
              accountId={accountId}
            />
          </CardContent>
        </Card>
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
    </div>
  );
}
