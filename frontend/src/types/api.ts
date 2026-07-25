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
  display_name?: string;
  currency?: string;
  logo?: string;
  created: string;
  last_accessed?: string;
  balances: AccountBalance[];
}

export interface AccountUpdate {
  display_name?: string;
}

/**
 * Unmodified bank transaction dict as stored by the sync. Keys are
 * snake_case for EnableBanking data, camelCase for mock/legacy
 * (GoCardless-era) data, and vary per bank — read it through
 * extractRawFields() in lib/raw-transaction.ts.
 */
export type RawTransactionData = Record<string, unknown>;

export interface Category {
  id: number;
  name: string;
  color: string;
  icon?: string;
  is_default: boolean;
  exclude_from_stats: boolean;
}

export interface CategoryCreate {
  name: string;
  color?: string;
  icon?: string;
  exclude_from_stats?: boolean;
}

export interface CategoryUpdate {
  name?: string;
  color?: string;
  icon?: string;
  exclude_from_stats?: boolean;
}

export interface CategorySuggestion {
  category: Category;
  score: number;
  confidence: "high" | "medium" | "low";
}

export interface CategoryStats {
  category_id: number | null;
  category_name: string;
  category_color: string;
  transaction_count: number;
  income: number;
  expenses: number;
  currency?: string | null;
}

// Mirrors leggen/api/models/accounts.py Transaction/TransactionSummary
export interface Transaction {
  transaction_id: string; // stable bank-provided transaction ID
  internal_transaction_id: string | null;
  account_id: string;
  transaction_value: number;
  transaction_currency: string;
  description: string;
  transaction_date: string;
  transaction_status: string;
  // Only present when summary_only=false
  institution_id?: string;
  iban?: string;
  category_id?: number;
  category_name?: string;
  category_color?: string;
  // Raw transaction data (only present when summary_only=false)
  raw_transaction?: RawTransactionData;
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

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
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
// Error envelope returned by every API error response.
// Mirrors ErrorResponse/ErrorField in leggen/api/models/common.py.
export interface ApiErrorField {
  field: string;
  message: string;
  type: string;
}

export interface ApiError {
  detail: string;
  code: string;
  status: number;
  errors?: ApiErrorField[];
}

export interface HealthData {
  status: string;
  config_loaded?: boolean;
  version?: string;
  message?: string;
}

// Version information from root endpoint
export interface VersionData {
  message: string;
  version: string;
}

// Analytics data types
export interface TransactionStats {
  date_from: string;
  date_to: string;
  total_transactions: number;
  booked_transactions: number;
  pending_transactions: number;
  /** Money totals cover only the dominant currency of the filtered set. */
  currency?: string | null;
  total_income: number;
  total_expenses: number;
  net_change: number;
  average_transaction: number;
  accounts_included: number;
}

export interface MonthlyStats {
  month: string;
  income: number;
  expenses: number;
  net: number;
  currency?: string | null;
}

// Sync operations types
export interface SyncOperation {
  id: number;
  started_at: string;
  completed_at?: string;
  success?: boolean;
  accounts_processed: number;
  transactions_added: number;
  transactions_updated: number;
  balances_updated: number;
  duration_seconds?: number;
  errors: string[];
  logs: string[];
  trigger_type: "manual" | "scheduled" | "api";
}

export interface SyncResult {
  success: boolean;
  accounts_processed: number;
  transactions_added: number;
  transactions_updated: number;
  balances_updated: number;
  duration_seconds: number;
  errors: string[];
  started_at: string;
  completed_at: string;
}

// Bank-related types
export interface BankInstitution {
  name: string;
  country: string;
  bic?: string;
  logo?: string;
  psu_types: string[];
  maximum_consent_validity?: number;
}

export interface BankAuthResponse {
  url: string;
}

export interface BankConnectionStatus {
  session_id: string;
  aspsp_name: string;
  aspsp_country: string;
  accounts_count: number;
  created_at: string;
  valid_until?: string;
  status: string;
  days_until_expiry?: number | null;
}

export interface Country {
  code: string;
  name: string;
}

// Backup types
export interface S3Config {
  access_key_id: string;
  secret_access_key: string;
  bucket_name: string;
  region: string;
  endpoint_url?: string;
  path_style: boolean;
  enabled: boolean;
}

export interface BackupSettings {
  s3?: S3Config;
}

export interface BackupTest {
  service: string;
  config: S3Config;
}

export interface BackupInfo {
  key: string;
  last_modified: string;
  size: number;
}

export interface BackupOperation {
  operation: string;
  backup_key?: string;
}

// Auth types
export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// Sync schedule types
export interface ScheduleSettings {
  enabled: boolean;
  hour: number;
  minute: number;
  cron?: string | null;
  next_sync_time?: string | null;
}
