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

export interface RawTransactionData {
  transactionId?: string;
  bookingDate?: string;
  valueDate?: string;
  bookingDateTime?: string;
  valueDateTime?: string;
  transactionAmount?: {
    amount: string;
    currency: string;
  };
  currencyExchange?: {
    instructedAmount?: {
      amount: string;
      currency: string;
    };
    sourceCurrency?: string;
    exchangeRate?: string;
    unitCurrency?: string;
    targetCurrency?: string;
  };
  creditorName?: string;
  debtorName?: string;
  debtorAccount?: {
    iban?: string;
  };
  remittanceInformationUnstructuredArray?: string[];
  proprietaryBankTransactionCode?: string;
  balanceAfterTransaction?: {
    balanceAmount: {
      amount: string;
      currency: string;
    };
    balanceType: string;
  };
  internalTransactionId?: string;
  [key: string]: unknown; // Allow additional fields
}

// Transaction enrichment types
export interface TransactionEnrichment {
  clean_name?: string;
  category?: string;
  logo_url?: string;
}

export interface TransactionEnrichmentUpdate {
  clean_name?: string;
  category?: string;
  logo_url?: string;
}

// Type for analytics transaction data
export interface AnalyticsTransaction {
  transaction_id: string;
  date: string;
  description: string;
  amount: number;
  currency: string;
  status: string;
  account_id: string;
  enrichment?: TransactionEnrichment;
}

export interface Transaction {
  transaction_id: string; // NEW: stable bank-provided transaction ID
  internal_transaction_id: string | null; // OLD: unstable GoCardless ID
  account_id: string;
  transaction_value: number;
  transaction_currency: string;
  description: string;
  transaction_date: string;
  transaction_status: string;
  // Optional fields that may be present in some transactions
  institution_id?: string;
  iban?: string;
  booking_date?: string;
  value_date?: string;
  creditor_name?: string;
  debtor_name?: string;
  reference?: string;
  category?: string;
  created_at?: string;
  updated_at?: string;
  // Raw transaction data (only present when summary_only=false)
  raw_transaction?: RawTransactionData;
  // Enrichment data
  enrichment?: TransactionEnrichment;
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
  pagination?: {
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
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
  version?: string;
  message?: string;
  error?: string;
}

// Version information from root endpoint
export interface VersionData {
  message: string;
  version: string;
}

// Analytics data types
export interface TransactionStats {
  period_days: number;
  total_transactions: number;
  booked_transactions: number;
  pending_transactions: number;
  total_income: number;
  total_expenses: number;
  net_change: number;
  average_transaction: number;
  accounts_included: number;
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

export interface SyncOperationsResponse {
  operations: SyncOperation[];
  count: number;
}

// Bank-related types
export interface BankInstitution {
  id: string;
  name: string;
  bic?: string;
  transaction_total_days: number;
  countries: string[];
  logo?: string;
}

export interface BankRequisition {
  id: string;
  institution_id: string;
  status: string;
  status_display?: string;
  created: string;
  link: string;
  accounts: string[];
}

export interface BankConnectionStatus {
  bank_id: string;
  bank_name: string;
  status: string;
  status_display: string;
  created_at: string;
  requisition_id: string;
  accounts_count: number;
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
