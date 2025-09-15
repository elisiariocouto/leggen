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

// Type for analytics transaction data
export interface AnalyticsTransaction {
  transaction_id: string;
  date: string;
  description: string;
  amount: number;
  currency: string;
  status: string;
  account_id: string;
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
  message?: string;
  error?: string;
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
