import type { Account } from "../types/api";

// Known institution_id → friendly bank name mappings; anything unknown
// falls back to the part before the first underscore.
const BANK_NAMES: Record<string, string> = {
  REVOLUT_REVOLT21: "Revolut",
  NUBANK_NUPBBR25: "Nu Pagamentos",
  BANCOBPI_BBPIPTPL: "Banco BPI",
};

export function getBankName(institutionId: string): string {
  return BANK_NAMES[institutionId] || institutionId.split("_")[0];
}

export function getAccountDisplayName(account: Account): string {
  const bankName = getBankName(account.institution_id);
  const accountName =
    account.display_name ||
    account.name ||
    `Account ${account.id.split("-")[1]}`;
  return `${bankName} - ${accountName}`;
}
