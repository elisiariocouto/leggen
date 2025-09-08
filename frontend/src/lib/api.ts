import axios from 'axios';
import type { Account, Transaction, Balance, ApiResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  // Get all accounts
  getAccounts: async (): Promise<Account[]> => {
    const response = await api.get<ApiResponse<Account[]>>('/accounts');
    return response.data.data;
  },

  // Get account by ID
  getAccount: async (id: string): Promise<Account> => {
    const response = await api.get<ApiResponse<Account>>(`/accounts/${id}`);
    return response.data.data;
  },

  // Get all balances
  getBalances: async (): Promise<Balance[]> => {
    const response = await api.get<ApiResponse<Balance[]>>('/balances');
    return response.data.data;
  },

  // Get balances for specific account
  getAccountBalances: async (accountId: string): Promise<Balance[]> => {
    const response = await api.get<ApiResponse<Balance[]>>(`/accounts/${accountId}/balances`);
    return response.data.data;
  },

  // Get transactions with optional filters
  getTransactions: async (params?: {
    accountId?: string;
    startDate?: string;
    endDate?: string;
    page?: number;
    perPage?: number;
    search?: string;
  }): Promise<Transaction[]> => {
    const queryParams = new URLSearchParams();

    if (params?.accountId) queryParams.append('account_id', params.accountId);
    if (params?.startDate) queryParams.append('start_date', params.startDate);
    if (params?.endDate) queryParams.append('end_date', params.endDate);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.perPage) queryParams.append('per_page', params.perPage.toString());
    if (params?.search) queryParams.append('search', params.search);

    const response = await api.get<ApiResponse<Transaction[]>>(`/transactions?${queryParams.toString()}`);
    return response.data.data;
  },

  // Get transaction by ID
  getTransaction: async (id: string): Promise<Transaction> => {
    const response = await api.get<ApiResponse<Transaction>>(`/transactions/${id}`);
    return response.data.data;
  },
};

export default apiClient;
