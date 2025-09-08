import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Filter,
  Search,
  TrendingUp,
  TrendingDown,
  Calendar,
  RefreshCw,
  AlertCircle,
  X
} from 'lucide-react';
import { apiClient } from '../lib/api';
import { formatCurrency, formatDate } from '../lib/utils';
import LoadingSpinner from './LoadingSpinner';
import type { Account, Transaction } from '../types/api';

export default function TransactionsList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAccount, setSelectedAccount] = useState<string>('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const {
    data: accounts
  } = useQuery<Account[]>({
    queryKey: ['accounts'],
    queryFn: apiClient.getAccounts,
  });

  const {
    data: transactions,
    isLoading: transactionsLoading,
    error: transactionsError,
    refetch: refetchTransactions
  } = useQuery<Transaction[]>({
    queryKey: ['transactions', selectedAccount, startDate, endDate],
    queryFn: () => apiClient.getTransactions({
      accountId: selectedAccount || undefined,
      startDate: startDate || undefined,
      endDate: endDate || undefined,
    }),
  });

  const filteredTransactions = (transactions || []).filter(transaction => {
    // Additional validation (API client should have already filtered out invalid ones)
    if (!transaction || !transaction.account_id) {
      console.warn('Invalid transaction found after API filtering:', transaction);
      return false;
    }

    const description = transaction.description || '';
    const creditorName = transaction.creditor_name || '';
    const debtorName = transaction.debtor_name || '';
    const reference = transaction.reference || '';

    const matchesSearch = searchTerm === '' ||
      description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      creditorName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      debtorName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      reference.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesSearch;
  });

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedAccount('');
    setStartDate('');
    setEndDate('');
  };

  const hasActiveFilters = searchTerm || selectedAccount || startDate || endDate;

  if (transactionsLoading) {
    return (
      <div className="bg-white rounded-lg shadow">
        <LoadingSpinner message="Loading transactions..." />
      </div>
    );
  }

  if (transactionsError) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center text-center">
          <div>
            <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load transactions</h3>
            <p className="text-gray-600 mb-4">
              Unable to fetch transactions from the Leggen API.
            </p>
            <button
              onClick={() => refetchTransactions()}
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

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">Transactions</h3>
            <div className="flex items-center space-x-2">
              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="inline-flex items-center px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                >
                  <X className="h-3 w-3 mr-1" />
                  Clear filters
                </button>
              )}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="inline-flex items-center px-3 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
              >
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </button>
            </div>
          </div>
        </div>

        {showFilters && (
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Search
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Description, name, reference..."
                    className="pl-10 pr-3 py-2 w-full border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Account Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Account
                </label>
                <select
                  value={selectedAccount}
                  onChange={(e) => setSelectedAccount(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All accounts</option>
                   {accounts?.map((account) => (
                     <option key={account.id} value={account.id}>
                       {account.name || 'Unnamed Account'} ({account.institution_id})
                     </option>
                   ))}
                </select>
              </div>

              {/* Start Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date
                </label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="pl-10 pr-3 py-2 w-full border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              {/* End Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date
                </label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="pl-10 pr-3 py-2 w-full border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results Summary */}
        <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
          <p className="text-sm text-gray-600">
            Showing {filteredTransactions.length} transaction{filteredTransactions.length !== 1 ? 's' : ''}
            {selectedAccount && accounts && (
              <span className="ml-1">
                for {accounts.find(acc => acc.id === selectedAccount)?.name}
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Transactions List */}
      {filteredTransactions.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <div className="text-gray-400 mb-4">
            <TrendingUp className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No transactions found</h3>
          <p className="text-gray-600">
            {hasActiveFilters ?
              "Try adjusting your filters to see more results." :
              "No transactions are available for the selected criteria."
            }
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow divide-y divide-gray-200">
          {filteredTransactions.map((transaction) => {
            const account = accounts?.find(acc => acc.id === transaction.account_id);
            const isPositive = transaction.amount > 0;

            return (
              <div key={transaction.internal_transaction_id || `${transaction.account_id}-${transaction.date}-${transaction.amount}`} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-start space-x-3">
                      <div className={`p-2 rounded-full ${
                        isPositive ? 'bg-green-100' : 'bg-red-100'
                      }`}>
                        {isPositive ? (
                          <TrendingUp className="h-4 w-4 text-green-600" />
                        ) : (
                          <TrendingDown className="h-4 w-4 text-red-600" />
                        )}
                      </div>

                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900 mb-1">
                          {transaction.description}
                        </h4>

                         <div className="text-xs text-gray-500 space-y-1">
                           {account && (
                             <p>{account.name || 'Unnamed Account'} • {account.institution_id}</p>
                           )}

                          {(transaction.creditor_name || transaction.debtor_name) && (
                            <p>
                              {isPositive ? 'From: ' : 'To: '}
                              {transaction.creditor_name || transaction.debtor_name}
                            </p>
                          )}

                          {transaction.reference && (
                            <p>Ref: {transaction.reference}</p>
                          )}

                          {transaction.internal_transaction_id && (
                            <p>ID: {transaction.internal_transaction_id}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="text-right ml-4">
                    <p className={`text-lg font-semibold ${
                      isPositive ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {isPositive ? '+' : ''}{formatCurrency(transaction.amount, transaction.currency)}
                    </p>
                    <p className="text-sm text-gray-500">
                      {transaction.date ? formatDate(transaction.date) : 'No date'}
                    </p>
                    {transaction.booking_date && transaction.booking_date !== transaction.date && (
                      <p className="text-xs text-gray-400">
                        Booked: {formatDate(transaction.booking_date)}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
