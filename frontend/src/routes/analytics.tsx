import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  CreditCard,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  Users,
} from "lucide-react";
import apiClient from "../lib/api";
import StatCard from "../components/analytics/StatCard";
import BalanceChart from "../components/analytics/BalanceChart";
import TransactionDistribution from "../components/analytics/TransactionDistribution";
import MonthlyTrends from "../components/analytics/MonthlyTrends";

function AnalyticsDashboard() {
  // Fetch analytics data
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["transaction-stats"],
    queryFn: () => apiClient.getTransactionStats(365), // Last year
  });

  const { data: accounts, isLoading: accountsLoading } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => apiClient.getAccounts(),
  });

  const { data: balances, isLoading: balancesLoading } = useQuery({
    queryKey: ["balances"],
    queryFn: () => apiClient.getBalances(),
  });

  const isLoading = statsLoading || accountsLoading || balancesLoading;

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-48 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="h-96 bg-gray-200 rounded"></div>
            <div className="h-96 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const totalBalance = accounts?.reduce((sum, account) => {
    const closingBalance = account.balances.find(
      (balance) => balance.balance_type === "closingBooked"
    );
    return sum + (closingBalance?.amount || 0);
  }, 0) || 0;

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Overview of your financial data and spending patterns
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Balance"
          value={`€${totalBalance.toLocaleString()}`}
          subtitle={`Across ${accounts?.length || 0} accounts`}
          icon={DollarSign}
        />
        <StatCard
          title="Total Transactions"
          value={stats?.total_transactions || 0}
          subtitle={`Last ${stats?.period_days || 0} days`}
          icon={Activity}
        />
        <StatCard
          title="Total Income"
          value={`€${(stats?.total_income || 0).toLocaleString()}`}
          subtitle="Inflows this period"
          icon={TrendingUp}
          className="border-green-200"
        />
        <StatCard
          title="Total Expenses"
          value={`€${(stats?.total_expenses || 0).toLocaleString()}`}
          subtitle="Outflows this period"
          icon={TrendingDown}
          className="border-red-200"
        />
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Net Change"
          value={`€${(stats?.net_change || 0).toLocaleString()}`}
          subtitle="Income minus expenses"
          icon={CreditCard}
          className={
            (stats?.net_change || 0) >= 0 ? "border-green-200" : "border-red-200"
          }
        />
        <StatCard
          title="Average Transaction"
          value={`€${Math.abs(stats?.average_transaction || 0).toLocaleString()}`}
          subtitle="Per transaction"
          icon={Activity}
        />
        <StatCard
          title="Active Accounts"
          value={stats?.accounts_included || 0}
          subtitle="With recent activity"
          icon={Users}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <BalanceChart data={balances || []} accounts={accounts || []} />
        </div>
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <TransactionDistribution accounts={accounts || []} />
        </div>
      </div>

      {/* Monthly Trends */}
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <MonthlyTrends />
      </div>

      {/* Summary Section */}
      {stats && (
        <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
          <h3 className="text-lg font-medium text-blue-900 mb-4">
            Period Summary ({stats.period_days} days)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-blue-700 font-medium">Booked Transactions</p>
              <p className="text-blue-900">{stats.booked_transactions}</p>
            </div>
            <div>
              <p className="text-blue-700 font-medium">Pending Transactions</p>
              <p className="text-blue-900">{stats.pending_transactions}</p>
            </div>
            <div>
              <p className="text-blue-700 font-medium">Transaction Ratio</p>
              <p className="text-blue-900">
                {stats.total_transactions > 0
                  ? `${Math.round(
                      (stats.booked_transactions / stats.total_transactions) * 100
                    )}% booked`
                  : "No transactions"}
              </p>
            </div>
            <div>
              <p className="text-blue-700 font-medium">Spend Rate</p>
              <p className="text-blue-900">
                €{((stats.total_expenses || 0) / stats.period_days).toFixed(2)}/day
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export const Route = createFileRoute("/analytics")({
  component: AnalyticsDashboard,
});
