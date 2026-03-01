import axios from "axios";
import type {
  Account,
  Transaction,
  Balance,
  PaginatedResponse,
  NotificationSettings,
  NotificationTest,
  NotificationService,
  NotificationServicesResponse,
  HealthData,
  AccountUpdate,
  TransactionStats,
  SyncOperationsResponse,
  BankInstitution,
  BankConnectionStatus,
  BankAuthResponse,
  Country,
  BackupSettings,
  BackupTest,
  BackupInfo,
  BackupOperation,
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
    const response = await api.get<Account[]>("/accounts");
    return response.data;
  },

  // Update account details
  updateAccount: async (
    id: string,
    updates: AccountUpdate,
  ): Promise<{ id: string; display_name?: string }> => {
    const response = await api.put<{ id: string; display_name?: string }>(
      `/accounts/${id}`,
      updates,
    );
    return response.data;
  },

  // Get all balances
  getBalances: async (): Promise<Balance[]> => {
    const response = await api.get<Balance[]>("/balances");
    return response.data;
  },

  // Get historical balances for balance progression chart
  getHistoricalBalances: async (
    days?: number,
    accountId?: string,
  ): Promise<Balance[]> => {
    const queryParams = new URLSearchParams();
    if (days) queryParams.append("days", days.toString());
    if (accountId) queryParams.append("account_id", accountId);

    const response = await api.get<Balance[]>(
      `/balances/history?${queryParams.toString()}`,
    );
    return response.data;
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
    minAmount?: number;
    maxAmount?: number;
  }): Promise<PaginatedResponse<Transaction>> => {
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
    if (params?.minAmount !== undefined) {
      queryParams.append("min_amount", params.minAmount.toString());
    }
    if (params?.maxAmount !== undefined) {
      queryParams.append("max_amount", params.maxAmount.toString());
    }

    const response = await api.get<PaginatedResponse<Transaction>>(
      `/transactions?${queryParams.toString()}`,
    );
    return response.data;
  },

  // Get notification settings
  getNotificationSettings: async (): Promise<NotificationSettings> => {
    const response = await api.get<NotificationSettings>(
      "/notifications/settings",
    );
    return response.data;
  },

  // Update notification settings
  updateNotificationSettings: async (
    settings: NotificationSettings,
  ): Promise<NotificationSettings> => {
    const response = await api.put<NotificationSettings>(
      "/notifications/settings",
      settings,
    );
    return response.data;
  },

  // Test notification
  testNotification: async (test: NotificationTest): Promise<void> => {
    await api.post("/notifications/test", test);
  },

  // Get notification services
  getNotificationServices: async (): Promise<NotificationService[]> => {
    const response = await api.get<NotificationServicesResponse>(
      "/notifications/services",
    );
    // Convert object to array format
    const servicesData = response.data;
    return Object.values(servicesData);
  },

  // Delete notification service
  deleteNotificationService: async (service: string): Promise<void> => {
    await api.delete(`/notifications/settings/${service}`);
  },

  // Health check
  getHealth: async (): Promise<HealthData> => {
    const response = await api.get<HealthData>("/health");
    return response.data;
  },

  // Analytics endpoints
  getTransactionStats: async (days?: number): Promise<TransactionStats> => {
    const queryParams = new URLSearchParams();
    if (days) queryParams.append("days", days.toString());

    const response = await api.get<TransactionStats>(
      `/transactions/stats?${queryParams.toString()}`,
    );
    return response.data;
  },

  // Get monthly transaction statistics (pre-calculated)
  getMonthlyTransactionStats: async (
    days?: number,
  ): Promise<
    Array<{
      month: string;
      income: number;
      expenses: number;
      net: number;
    }>
  > => {
    const queryParams = new URLSearchParams();
    if (days) queryParams.append("days", days.toString());

    const response = await api.get<
      Array<{
        month: string;
        income: number;
        expenses: number;
        net: number;
      }>
    >(`/transactions/monthly-stats?${queryParams.toString()}`);
    return response.data;
  },

  // Get sync operations history
  getSyncOperations: async (
    limit: number = 50,
    offset: number = 0,
  ): Promise<SyncOperationsResponse> => {
    const response = await api.get<SyncOperationsResponse>(
      `/sync/operations?limit=${limit}&offset=${offset}`,
    );
    return response.data;
  },

  // Bank management endpoints
  getBankInstitutions: async (country: string): Promise<BankInstitution[]> => {
    const response = await api.get<BankInstitution[]>(
      `/banks/institutions?country=${country}`,
    );
    return response.data;
  },

  getBankConnectionsStatus: async (): Promise<BankConnectionStatus[]> => {
    const response = await api.get<BankConnectionStatus[]>("/banks/status");
    return response.data;
  },

  createBankConnection: async (
    aspspName: string,
    aspspCountry: string,
    psuType: string = "personal",
    redirectUrl?: string,
  ): Promise<BankAuthResponse> => {
    const finalRedirectUrl =
      redirectUrl || `${window.location.origin}/bank-connected`;

    const response = await api.post<BankAuthResponse>("/banks/connect", {
      aspsp_name: aspspName,
      aspsp_country: aspspCountry,
      redirect_url: finalRedirectUrl,
      psu_type: psuType,
    });
    return response.data;
  },

  exchangeAuthCode: async (
    code: string,
  ): Promise<Record<string, unknown>> => {
    const response = await api.post<Record<string, unknown>>(
      "/banks/callback",
      { code },
    );
    return response.data;
  },

  deleteBankConnection: async (sessionId: string): Promise<void> => {
    await api.delete(`/banks/connections/${sessionId}`);
  },

  getSupportedCountries: async (): Promise<Country[]> => {
    const response = await api.get<Country[]>("/banks/countries");
    return response.data;
  },

  // Backup endpoints
  getBackupSettings: async (): Promise<BackupSettings> => {
    const response = await api.get<BackupSettings>("/backup/settings");
    return response.data;
  },

  updateBackupSettings: async (
    settings: BackupSettings,
  ): Promise<BackupSettings> => {
    const response = await api.put<BackupSettings>(
      "/backup/settings",
      settings,
    );
    return response.data;
  },

  testBackupConnection: async (
    test: BackupTest,
  ): Promise<{ connected?: boolean; success?: boolean; message?: string }> => {
    const response = await api.post<{
      connected?: boolean;
      success?: boolean;
      message?: string;
    }>("/backup/test", test);
    return response.data;
  },

  listBackups: async (): Promise<BackupInfo[]> => {
    const response = await api.get<BackupInfo[]>("/backup/list");
    return response.data;
  },

  performBackupOperation: async (
    operation: BackupOperation,
  ): Promise<{
    operation: string;
    completed: boolean;
    success?: boolean;
    message?: string;
  }> => {
    const response = await api.post<{
      operation: string;
      completed: boolean;
      success?: boolean;
      message?: string;
    }>("/backup/operation", operation);
    return response.data;
  },
};

export default apiClient;
