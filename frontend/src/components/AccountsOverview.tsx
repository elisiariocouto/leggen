import { useQuery } from '@tanstack/react-query';
import {
  CreditCard,
  TrendingUp,
  TrendingDown,
  Building2,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { apiClient } from '../lib/api';
import { formatCurrency, formatDate } from '../lib/utils';
import LoadingSpinner from './LoadingSpinner';
import type { Account, Balance } from '../types/api';

export default function AccountsOverview() {
  const {
    data: accounts,
    isLoading: accountsLoading,
    error: accountsError,
    refetch: refetchAccounts
  } = useQuery<Account[]>({
    queryKey: ['accounts'],
    queryFn: apiClient.getAccounts,
  });

  const {
    data: balances
  } = useQuery<Balance[]>({
    queryKey: ['balances'],
    queryFn: () => apiClient.getBalances(),
  });

  if (accountsLoading) {
    return (
      <div className="bg-white rounded-lg shadow">
        <LoadingSpinner message="Loading accounts..." />
      </div>
    );
  }

  if (accountsError) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center text-center">
          <div>
            <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load accounts</h3>
            <p className="text-gray-600 mb-4">
              Unable to connect to the Leggen API. Make sure the server is running on localhost:8000.
            </p>
            <button
              onClick={() => refetchAccounts()}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const totalBalance = accounts?.reduce((sum, account) => sum + (account.balance || 0), 0) || 0;
  const totalAccounts = accounts?.length || 0;
  const uniqueBanks = new Set(accounts?.map(acc => acc.bank_name) || []).size;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Balance</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(totalBalance)}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Accounts</p>
              <p className="text-2xl font-bold text-gray-900">{totalAccounts}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <CreditCard className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Connected Banks</p>
              <p className="text-2xl font-bold text-gray-900">{uniqueBanks}</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <Building2 className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Accounts List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Bank Accounts</h3>
          <p className="text-sm text-gray-600">Manage your connected bank accounts</p>
        </div>

        {!accounts || accounts.length === 0 ? (
          <div className="p-6 text-center">
            <CreditCard className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No accounts found</h3>
            <p className="text-gray-600">
              Connect your first bank account to get started with Leggen.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {accounts.map((account) => {
              const accountBalance = balances?.find(b => b.account_id === account.id);
              const balance = account.balance || accountBalance?.balance_amount || 0;
              const isPositive = balance >= 0;

              return (
                <div key={account.id} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="p-3 bg-gray-100 rounded-full">
                        <Building2 className="h-6 w-6 text-gray-600" />
                      </div>
                      <div>
                        <h4 className="text-lg font-medium text-gray-900">
                          {account.name}
                        </h4>
                        <p className="text-sm text-gray-600">
                          {account.bank_name} • {account.account_type}
                        </p>
                        {account.iban && (
                          <p className="text-xs text-gray-500 mt-1">
                            IBAN: {account.iban}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="flex items-center space-x-2">
                        {isPositive ? (
                          <TrendingUp className="h-4 w-4 text-green-500" />
                        ) : (
                          <TrendingDown className="h-4 w-4 text-red-500" />
                        )}
                        <p className={`text-lg font-semibold ${
                          isPositive ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatCurrency(balance, account.currency)}
                        </p>
                      </div>
                      <p className="text-sm text-gray-500">
                        Updated {formatDate(account.updated_at)}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
