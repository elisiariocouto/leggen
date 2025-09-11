import axios from "axios";
import type {
  Account,
  Transaction,
  Balance,
  ApiResponse,
  NotificationSettings,
  NotificationTest,
  NotificationService,
  NotificationServicesResponse,
  HealthData,
  AccountUpdate,
} from "../types/api";

// Use VITE_API_URL for development, relative URLs for production
const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const apiClient = {
  // Get all accounts
  getAccounts: async (): Promise<Account[]> => {
    const response = await api.get<ApiResponse<Account[]>>("/accounts");
    return response.data.data;
  },

  // Get account by ID
  getAccount: async (id: string): Promise<Account> => {
    const response = await api.get<ApiResponse<Account>>(`/accounts/${id}`);
    return response.data.data;
  },

  // Update account details
  updateAccount: async (
    id: string,
    updates: AccountUpdate,
  ): Promise<{ id: string; name?: string }> => {
    const response = await api.put<ApiResponse<{ id: string; name?: string }>>(
      `/accounts/${id}`,
      updates,
    );
    return response.data.data;
  },

  // Get all balances
  getBalances: async (): Promise<Balance[]> => {
    const response = await api.get<ApiResponse<Balance[]>>("/balances");
    return response.data.data;
  },

  // Get balances for specific account
  getAccountBalances: async (accountId: string): Promise<Balance[]> => {
    const response = await api.get<ApiResponse<Balance[]>>(
      `/accounts/${accountId}/balances`,
    );
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
    summaryOnly?: boolean;
  }): Promise<ApiResponse<Transaction[]>> => {
    const queryParams = new URLSearchParams();

    if (params?.accountId) queryParams.append("account_id", params.accountId);
    if (params?.startDate) queryParams.append("date_from", params.startDate);
    if (params?.endDate) queryParams.append("date_to", params.endDate);
    if (params?.page) queryParams.append("page", params.page.toString());
    if (params?.perPage)
      queryParams.append("per_page", params.perPage.toString());
    if (params?.search) queryParams.append("search", params.search);
    if (params?.summaryOnly !== undefined) {
      queryParams.append("summary_only", params.summaryOnly.toString());
    }

    const response = await api.get<ApiResponse<Transaction[]>>(
      `/transactions?${queryParams.toString()}`,
    );
    return response.data;
  },

  // Get transaction by ID
  getTransaction: async (id: string): Promise<Transaction> => {
    const response = await api.get<ApiResponse<Transaction>>(
      `/transactions/${id}`,
    );
    return response.data.data;
  },

  // Get notification settings
  getNotificationSettings: async (): Promise<NotificationSettings> => {
    const response = await api.get<ApiResponse<NotificationSettings>>(
      "/notifications/settings",
    );
    return response.data.data;
  },

  // Update notification settings
  updateNotificationSettings: async (
    settings: NotificationSettings,
  ): Promise<NotificationSettings> => {
    const response = await api.put<ApiResponse<NotificationSettings>>(
      "/notifications/settings",
      settings,
    );
    return response.data.data;
  },

  // Test notification
  testNotification: async (test: NotificationTest): Promise<void> => {
    await api.post("/notifications/test", test);
  },

  // Get notification services
  getNotificationServices: async (): Promise<NotificationService[]> => {
    const response = await api.get<ApiResponse<NotificationServicesResponse>>(
      "/notifications/services",
    );
    // Convert object to array format
    const servicesData = response.data.data;
    return Object.values(servicesData);
  },

  // Delete notification service
  deleteNotificationService: async (service: string): Promise<void> => {
    await api.delete(`/notifications/settings/${service}`);
  },

  // Health check
  getHealth: async (): Promise<HealthData> => {
    const response = await api.get<ApiResponse<HealthData>>("/health");
    return response.data.data;
  },
};

export default apiClient;
