import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { format } from "date-fns";
import { CreditCard, TrendingUp, TrendingDown } from "lucide-react";
import { apiClient } from "../../lib/api";
import { formatCurrency } from "../../lib/utils";
import StatCard from "./StatCard";
import CashFlowChart from "./CashFlowChart";
import NetWorthChart from "./NetWorthChart";
import TopMerchants from "./TopMerchants";
import RecurringPayments from "./RecurringPayments";
import SpendingByCategoryChart from "./SpendingByCategoryChart";
import CategoryMatrix from "./CategoryMatrix";
import CategoryDetail, { type SelectedCategory } from "./CategoryDetail";
import NeedsRule from "./NeedsRule";
import CoverageCard from "./CoverageCard";
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

  // A category picked from the stacked chart or the matrix opens its detail
  // panel; null is the uncategorized remainder, undefined nothing.
  const [selectedCategory, setSelectedCategory] =
    useState<SelectedCategory>(undefined);

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

      {/* Headline totals for the selected window, and how much of the
          spending the categories below can explain */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          isLoading={statsLoading}
          title="Income"
          value={formatCurrency(stats?.total_income || 0, statsCurrency)}
          subtitle={subtitle}
          icon={TrendingUp}
          iconColor="green"
          shouldBlur={true}
        />
        <StatCard
          isLoading={statsLoading}
          title="Expenses"
          value={formatCurrency(stats?.total_expenses || 0, statsCurrency)}
          subtitle={`${stats?.total_transactions ?? 0} transactions`}
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
        <CoverageCard
          dateFrom={startDate}
          dateTo={endDate}
          accountId={accountId}
        />
      </div>

      {/* Where does it go, month by month: the chart for the shape, the
          table for every number. Clicking either opens the category. */}
      <Card>
        <CardContent className="p-6">
          <SpendingByCategoryChart
            dateFrom={startDate}
            dateTo={endDate}
            accountId={accountId}
            onSelectCategory={setSelectedCategory}
          />
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-6">
          <CategoryMatrix
            dateFrom={startDate}
            dateTo={endDate}
            accountId={accountId}
            onSelectCategory={setSelectedCategory}
          />
        </CardContent>
      </Card>

      {/* What the categories still miss, and who gets the money overall */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardContent className="p-6">
            <NeedsRule
              dateFrom={startDate}
              dateTo={endDate}
              accountId={accountId}
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <TopMerchants
              dateFrom={startDate}
              dateTo={endDate}
              accountId={accountId}
            />
          </CardContent>
        </Card>
      </div>

      {/* Am I saving or burning, and what do I actually have */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardContent className="p-6">
            <CashFlowChart
              dateFrom={startDate}
              dateTo={endDate}
              accountId={accountId}
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <NetWorthChart
              dateFrom={startDate}
              dateTo={endDate}
              accountId={accountId}
            />
          </CardContent>
        </Card>
      </div>

      {/* What am I committed to */}
      <Card>
        <CardContent className="p-6">
          <RecurringPayments
            dateFrom={startDate}
            dateTo={endDate}
            accountId={accountId}
          />
        </CardContent>
      </Card>

      <CategoryDetail
        categoryId={selectedCategory}
        onClose={() => setSelectedCategory(undefined)}
        dateFrom={startDate}
        dateTo={endDate}
        accountId={accountId}
      />
    </div>
  );
}
