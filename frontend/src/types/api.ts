export interface AccountBalance {
  amount: number;
  currency: string;
  balance_type: string;
  last_change_date?: string;
}

export interface Account {
  id: string;
  institution_id: string;
  status: string;
  iban?: string;
  name?: string;
  currency?: string;
  created: string;
  last_accessed?: string;
  balances: AccountBalance[];
}

export interface Transaction {
  internal_transaction_id: string | null;
  account_id: string;
  amount: number;
  currency: string;
  description: string;
  date: string;
  status: string;
  // Optional fields that may be present in some transactions
  booking_date?: string;
  value_date?: string;
  creditor_name?: string;
  debtor_name?: string;
  reference?: string;
  category?: string;
  created_at?: string;
  updated_at?: string;
}

// Type for raw transaction data from API (before sanitization)
export interface RawTransaction {
  id?: string;
  internal_id?: string;
  account_id?: string;
  amount?: number;
  currency?: string;
  description?: string;
  transaction_date?: string;
  booking_date?: string;
  value_date?: string;
  creditor_name?: string;
  debtor_name?: string;
  reference?: string;
  category?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Balance {
  id: string;
  account_id: string;
  balance_amount: number;
  balance_type: string;
  currency: string;
  reference_date: string;
  created_at: string;
  updated_at: string;
}

export interface Bank {
  id: string;
  name: string;
  country_code: string;
  logo_url?: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Notification types
export interface DiscordConfig {
  webhook: string;
  enabled: boolean;
}

export interface TelegramConfig {
  token: string;
  chat_id: number;
  enabled: boolean;
}

export interface NotificationFilters {
  case_insensitive: string[];
  case_sensitive?: string[];
}

export interface NotificationSettings {
  discord?: DiscordConfig;
  telegram?: TelegramConfig;
  filters: NotificationFilters;
}

export interface NotificationTest {
  service: string;
  message?: string;
}

export interface NotificationService {
  name: string;
  enabled: boolean;
  configured: boolean;
  active?: boolean;
}

export interface NotificationServicesResponse {
  [serviceName: string]: NotificationService;
}

// Health check response data
export interface HealthData {
  status: string;
  config_loaded?: boolean;
  message?: string;
  error?: string;
}
