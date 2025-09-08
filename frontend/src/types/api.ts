export interface Account {
  id: string;
  name: string;
  bank_name: string;
  account_type: string;
  currency: string;
  balance?: number;
  iban?: string;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  internal_id?: string;
  account_id: string;
  amount: number;
  currency: string;
  description: string;
  transaction_date: string;
  booking_date?: string;
  value_date?: string;
  creditor_name?: string;
  debtor_name?: string;
  reference?: string;
  category?: string;
  created_at: string;
  updated_at: string;
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
  status: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
