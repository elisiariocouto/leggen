// Friendly names over the generated OpenAPI types in api.gen.ts.
// Regenerate with `just generate-api` (or `npm run generate:api` after
// dumping openapi.json) whenever the backend API models change — CI fails
// if the generated file is stale. Only add hand-written shapes here when
// the schema cannot express them (e.g. generics).
import type { components } from "./api.gen";

type Schemas = components["schemas"];

// Accounts and balances
export type Account = Schemas["AccountDetails"];
export type AccountBalance = Schemas["AccountBalance"];
export type AccountUpdate = Schemas["AccountUpdate"];
export type Balance = Schemas["Balance"];

// Transactions
export type Transaction = Schemas["Transaction"];

/**
 * Unmodified bank transaction dict as stored by the sync. Keys are
 * snake_case for EnableBanking data, camelCase for mock/legacy
 * (GoCardless-era) data, and vary per bank — read it through
 * extractRawFields() in lib/raw-transaction.ts.
 */
export type RawTransactionData = Transaction["raw_transaction"];

// Categories
export type Category = Schemas["Category"];
export type CategoryCreate = Schemas["CategoryCreate"];
export type CategoryUpdate = Schemas["CategoryUpdate"];
export type CategorySuggestion = Schemas["CategorySuggestion"];

// Analytics
export type CategoryStats = Schemas["CategoryStats"];
export type TransactionStats = Schemas["TransactionStats"];
export type MonthlyStats = Schemas["MonthlyStats"];

// OpenAPI cannot express generics, so the schema only holds concrete
// instantiations of PaginatedResponse. Rebuild the generic from one of
// them so envelope-field changes still flow through from the backend.
export type PaginatedResponse<T> = Omit<
  Schemas["PaginatedResponse_SyncOperation_"],
  "data"
> & { data: T[] };

// Notifications
export type DiscordConfig = Schemas["DiscordConfig"];
export type TelegramConfig = Schemas["TelegramConfig"];
export type NotificationFilters = Schemas["NotificationFilters"];
export type NotificationSettings = Schemas["NotificationSettings"];
export type NotificationTest = Schemas["NotificationTest"];
export type NotificationService = Schemas["NotificationServiceStatus"];
export type NotificationServicesResponse = Record<string, NotificationService>;

// Error envelope returned by every API error response
export type ApiError = Schemas["ErrorResponse"];
export type ApiErrorField = Schemas["ErrorField"];

// Health check response data
export type HealthData = Schemas["HealthStatus"];

// Sync
export type SyncOperation = Schemas["SyncOperation"];
export type SyncResult = Schemas["SyncResult"];
export type ScheduleSettings = Schemas["SyncScheduleResponse"];

// Banks
export type BankInstitution = Schemas["BankInstitution"];
export type BankAuthResponse = Schemas["BankAuthResponse"];
export type BankConnectionStatus = Schemas["BankConnectionStatus"];
export type Country = Schemas["Country"];

// Backups
export type S3Config = Schemas["S3Config"];
export type BackupSettings = Schemas["BackupSettings"];
export type BackupTest = Schemas["BackupTest"];
export type BackupInfo = Schemas["BackupInfo"];
export type BackupOperation = Schemas["BackupOperation"];

// Auth
export type LoginResponse = Schemas["LoginResponse"];
