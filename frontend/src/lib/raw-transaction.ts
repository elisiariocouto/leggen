import type { RawTransactionData } from "../types/api";

export interface RawCurrencyExchange {
  sourceCurrency?: string;
  targetCurrency?: string;
  exchangeRate?: string;
  instructedAmount?: { amount: string; currency: string };
}

export interface RawTransactionFields {
  bookingDate?: string;
  valueDate?: string;
  creditorName?: string;
  creditorIban?: string;
  debtorName?: string;
  debtorIban?: string;
  entryReference?: string;
  bankTransactionCode?: string;
  currencyExchange?: RawCurrencyExchange;
  balanceAfter?: { amount: number; currency: string };
}

type Raw = Record<string, unknown>;

function asRecord(value: unknown): Raw | undefined {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    return value as Raw;
  }
  return undefined;
}

function asString(value: unknown): string | undefined {
  if (typeof value === "string" && value.trim() !== "") return value;
  if (typeof value === "number") return String(value);
  return undefined;
}

/** First non-null value among the given keys (snake_case and camelCase). */
function pick(raw: Raw | undefined, ...keys: string[]): unknown {
  if (!raw) return undefined;
  for (const key of keys) {
    const value = raw[key];
    if (value !== undefined && value !== null) return value;
  }
  return undefined;
}

function pickString(raw: Raw | undefined, ...keys: string[]): string | undefined {
  return asString(pick(raw, ...keys));
}

function extractBankTransactionCode(raw: Raw): string | undefined {
  const value = pick(
    raw,
    "bank_transaction_code",
    "bankTransactionCode",
    "proprietaryBankTransactionCode",
  );
  const direct = asString(value);
  if (direct) return direct;
  // EnableBanking returns an object: {description?, code?, sub_code?}
  const record = asRecord(value);
  if (!record) return undefined;
  const description = pickString(record, "description");
  if (description) return description;
  const parts = [pickString(record, "code"), pickString(record, "sub_code", "subCode")];
  const joined = parts.filter(Boolean).join(" / ");
  return joined || undefined;
}

function extractCurrencyExchange(raw: Raw): RawCurrencyExchange | undefined {
  let value = pick(raw, "currency_exchange", "currencyExchange");
  // Some banks return a list of exchange legs — show the first
  if (Array.isArray(value)) value = value[0];
  const record = asRecord(value);
  if (!record) return undefined;

  const instructed = asRecord(pick(record, "instructed_amount", "instructedAmount"));
  const instructedAmount = asString(pick(instructed, "amount"));
  const instructedCurrency = asString(pick(instructed, "currency"));

  const exchange: RawCurrencyExchange = {
    sourceCurrency: pickString(record, "source_currency", "sourceCurrency"),
    targetCurrency: pickString(record, "target_currency", "targetCurrency"),
    exchangeRate: pickString(record, "exchange_rate", "exchangeRate"),
    instructedAmount:
      instructedAmount && instructedCurrency
        ? { amount: instructedAmount, currency: instructedCurrency }
        : undefined,
  };
  return Object.values(exchange).some((v) => v !== undefined) ? exchange : undefined;
}

function extractBalanceAfter(raw: Raw): { amount: number; currency: string } | undefined {
  const container = asRecord(
    pick(raw, "balance_after_transaction", "balanceAfterTransaction"),
  );
  const balanceAmount = asRecord(pick(container, "balance_amount", "balanceAmount"));
  const amount = asString(pick(balanceAmount, "amount"));
  const currency = asString(pick(balanceAmount, "currency"));
  if (amount === undefined || currency === undefined) return undefined;
  const parsed = Number.parseFloat(amount);
  if (Number.isNaN(parsed)) return undefined;
  return { amount: parsed, currency };
}

/**
 * Normalize a raw bank transaction blob into a flat, display-ready shape.
 * Every field is optional — banks send wildly different subsets, and the
 * blob's casing depends on its origin (snake_case for EnableBanking,
 * camelCase for mock/legacy data), so each field is read under both keys.
 */
export function extractRawFields(
  raw: RawTransactionData | undefined,
): RawTransactionFields {
  if (!raw) return {};

  const creditor = asRecord(pick(raw, "creditor"));
  const creditorAccount = asRecord(pick(raw, "creditor_account", "creditorAccount"));
  const debtor = asRecord(pick(raw, "debtor"));
  const debtorAccount = asRecord(pick(raw, "debtor_account", "debtorAccount"));

  return {
    bookingDate: pickString(raw, "booking_date", "bookingDate"),
    valueDate: pickString(raw, "value_date", "valueDate"),
    creditorName: pickString(creditor, "name") ?? pickString(raw, "creditorName"),
    creditorIban: pickString(creditorAccount, "iban"),
    debtorName: pickString(debtor, "name") ?? pickString(raw, "debtorName"),
    debtorIban: pickString(debtorAccount, "iban"),
    entryReference: pickString(raw, "entry_reference", "entryReference"),
    bankTransactionCode: extractBankTransactionCode(raw),
    currencyExchange: extractCurrencyExchange(raw),
    balanceAfter: extractBalanceAfter(raw),
  };
}
