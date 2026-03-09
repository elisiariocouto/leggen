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
  MonthlyStats,
  SyncOperationsResponse,
  SyncResult,
  BankInstitution,
  BankConnectionStatus,
  BankAuthResponse,
  Country,
  BackupSettings,
  BackupTest,
  BackupInfo,
  BackupOperation,
  ScheduleSettings,
  Category,
  CategoryCreate,
  CategoryUpdate,
  CategorySuggestion,
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

  // Delete account
  deleteAccount: async (
    accountId: string,
    deleteData: boolean = true,
  ): Promise<void> => {
    await api.delete(`/accounts/${accountId}`, {
      params: { delete_data: deleteData },
    });
  },

  // Get all balances
  getBalances: async (): Promise<Balance[]> => {
    const response = await api.get<Balance[]>("/balances");
    return response.data;
  },

  // Get historical balances for balance progression chart
  getHistoricalBalances: async (
    dateFrom: string,
    dateTo: string,
    accountId?: string,
  ): Promise<Balance[]> => {
    const queryParams = new URLSearchParams();
    queryParams.append("date_from", dateFrom);
    queryParams.append("date_to", dateTo);
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
  getTransactionStats: async (
    dateFrom?: string,
    dateTo?: string,
    accountId?: string,
    search?: string,
    minAmount?: number,
    maxAmount?: number,
  ): Promise<TransactionStats> => {
    const queryParams = new URLSearchParams();
    if (dateFrom) queryParams.append("date_from", dateFrom);
    if (dateTo) queryParams.append("date_to", dateTo);
    if (accountId) queryParams.append("account_id", accountId);
    if (search) queryParams.append("search", search);
    if (minAmount !== undefined)
      queryParams.append("min_amount", minAmount.toString());
    if (maxAmount !== undefined)
      queryParams.append("max_amount", maxAmount.toString());

    const response = await api.get<TransactionStats>(
      `/transactions/stats?${queryParams.toString()}`,
    );
    return response.data;
  },

  // Get monthly transaction statistics (group_by=month)
  getTransactionStatsByMonth: async (
    dateFrom: string,
    dateTo: string,
    accountId?: string,
  ): Promise<MonthlyStats[]> => {
    const queryParams = new URLSearchParams();
    queryParams.append("date_from", dateFrom);
    queryParams.append("date_to", dateTo);
    queryParams.append("group_by", "month");
    if (accountId) queryParams.append("account_id", accountId);

    const response = await api.get<MonthlyStats[]>(
      `/transactions/stats?${queryParams.toString()}`,
    );
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

  // Trigger sync
  triggerSync: async (params?: {
    account_ids?: string[];
    full_sync?: boolean;
  }): Promise<SyncResult> => {
    const response = await api.post<SyncResult>("/sync", params || {});
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

  // Sync schedule endpoints
  getScheduleSettings: async (): Promise<ScheduleSettings> => {
    const response = await api.get<ScheduleSettings>("/sync/schedule");
    return response.data;
  },

  updateScheduleSettings: async (
    settings: Omit<ScheduleSettings, "next_sync_time">,
  ): Promise<ScheduleSettings> => {
    const response = await api.put<ScheduleSettings>(
      "/sync/schedule",
      settings,
    );
    return response.data;
  },

  // Category endpoints
  getCategories: async (): Promise<Category[]> => {
    const response = await api.get<Category[]>("/categories");
    return response.data;
  },

  createCategory: async (data: CategoryCreate): Promise<Category> => {
    const response = await api.post<Category>("/categories", data);
    return response.data;
  },

  updateCategory: async (
    id: number,
    data: CategoryUpdate,
  ): Promise<Category> => {
    const response = await api.put<Category>(`/categories/${id}`, data);
    return response.data;
  },

  deleteCategory: async (id: number): Promise<void> => {
    await api.delete(`/categories/${id}`);
  },

  bulkAssignCategoryByDescription: async (
    categoryId: number,
    description: string,
  ): Promise<{ status: string; updated_count: number }> => {
    const response = await api.put<{ status: string; updated_count: number }>(
      "/transactions/bulk-categorize",
      { category_id: categoryId, description },
    );
    return response.data;
  },

  bulkRemoveCategoryByDescription: async (
    description: string,
  ): Promise<{ status: string; removed_count: number }> => {
    const response = await api.delete<{
      status: string;
      removed_count: number;
    }>("/transactions/bulk-categorize", { data: { description } });
    return response.data;
  },

  assignCategory: async (
    accountId: string,
    transactionId: string,
    categoryId: number,
  ): Promise<void> => {
    await api.put(`/transactions/${accountId}/${transactionId}/category`, {
      category_id: categoryId,
    });
  },

  removeCategory: async (
    accountId: string,
    transactionId: string,
  ): Promise<void> => {
    await api.delete(`/transactions/${accountId}/${transactionId}/category`);
  },

  getCategorySuggestions: async (
    accountId: string,
    transactionId: string,
  ): Promise<CategorySuggestion[]> => {
    const response = await api.get<CategorySuggestion[]>(
      `/transactions/${accountId}/${transactionId}/suggest-category`,
    );
    return response.data;
  },
};

export default apiClient;
