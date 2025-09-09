import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  CreditCard,
  TrendingUp,
  Activity,
  Menu,
  X,
  Home,
  List,
  BarChart3,
  Wifi,
  WifiOff
} from 'lucide-react';
import { apiClient } from '../lib/api';
import AccountsOverview from './AccountsOverview';
import TransactionsList from './TransactionsList';
import ErrorBoundary from './ErrorBoundary';
import { cn } from '../lib/utils';
import type { Account } from '../types/api';

type TabType = 'overview' | 'transactions' | 'analytics';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const { data: accounts } = useQuery<Account[]>({
    queryKey: ['accounts'],
    queryFn: apiClient.getAccounts,
  });

  const { data: healthStatus, isLoading: healthLoading, isError: healthError } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/health`);
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }
      return response.json();
    },
    refetchInterval: 30000, // Check every 30 seconds
    retry: 3,
  });

  const navigation = [
    { name: 'Overview', icon: Home, id: 'overview' as TabType },
    { name: 'Transactions', icon: List, id: 'transactions' as TabType },
    { name: 'Analytics', icon: BarChart3, id: 'analytics' as TabType },
  ];

  const totalBalance = accounts?.reduce((sum, account) => {
    // Get the first available balance from the balances array
    const primaryBalance = account.balances?.[0]?.amount || 0;
    return sum + primaryBalance;
  }, 0) || 0;

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <CreditCard className="h-8 w-8 text-blue-600" />
            <h1 className="text-xl font-bold text-gray-900">Leggen</h1>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 rounded-md text-gray-400 hover:text-gray-500"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <nav className="px-6 py-4">
          <div className="space-y-1">
            {navigation.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setSidebarOpen(false);
                }}
                className={cn(
                  "flex items-center w-full px-3 py-2 text-sm font-medium rounded-md transition-colors",
                  activeTab === item.id
                    ? "bg-blue-100 text-blue-700"
                    : "text-gray-700 hover:text-gray-900 hover:bg-gray-100"
                )}
              >
                <item.icon className="mr-3 h-5 w-5" />
                {item.name}
              </button>
            ))}
          </div>
        </nav>

        {/* Account Summary in Sidebar */}
        <div className="px-6 py-4 border-t border-gray-200 mt-auto">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">Total Balance</span>
              <TrendingUp className="h-4 w-4 text-green-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'EUR',
              }).format(totalBalance)}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {accounts?.length || 0} accounts
            </p>
          </div>
        </div>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between h-16 px-6">
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-1 rounded-md text-gray-400 hover:text-gray-500"
              >
                <Menu className="h-6 w-6" />
              </button>
              <h2 className="text-lg font-semibold text-gray-900 lg:ml-0 ml-4">
                {navigation.find(item => item.id === activeTab)?.name}
              </h2>
            </div>
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1">
                {healthLoading ? (
                  <>
                    <Activity className="h-4 w-4 text-yellow-500 animate-pulse" />
                    <span className="text-sm text-gray-600">Checking...</span>
                  </>
                ) : healthError || !healthStatus?.success ? (
                  <>
                    <WifiOff className="h-4 w-4 text-red-500" />
                    <span className="text-sm text-red-500">Disconnected</span>
                  </>
                ) : (
                  <>
                    <Wifi className="h-4 w-4 text-green-500" />
                    <span className="text-sm text-gray-600">Connected</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Main content area */}
        <main className="flex-1 overflow-y-auto p-6">
          <ErrorBoundary>
            {activeTab === 'overview' && <AccountsOverview />}
            {activeTab === 'transactions' && <TransactionsList />}
            {activeTab === 'analytics' && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Analytics</h3>
                <p className="text-gray-600">Analytics dashboard coming soon...</p>
              </div>
            )}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
