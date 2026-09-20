"""Data processing layer for all transformation logic."""

import re
from datetime import datetime
from typing import Any

from loguru import logger

from leggen.errors import describe_exception
from leggen.services.enablebanking_service import EnableBankingService

# --- Account enrichment ---


async def enrich_account_details(
    account_details: dict[str, Any],
    balances: dict[str, Any],
    aspsp_country: str | None = None,
    enablebanking_service: EnableBankingService | None = None,
) -> dict[str, Any]:
    """
    Enrich account details with currency from balances and institution logo.

    Args:
        account_details: Raw account details from EnableBanking
        balances: Balance data containing currency information
        aspsp_country: Country code for looking up institution logo
        enablebanking_service: EnableBanking service instance for fetching logos

    Returns:
        Enriched account details with currency and logo added
    """
    enriched_account = account_details.copy()

    # Extract currency from first balance
    currency = _extract_currency_from_balances(balances)
    if currency:
        enriched_account["currency"] = currency

    # Fetch and add institution logo
    institution_id = enriched_account.get("institution_id")
    if institution_id and aspsp_country and enablebanking_service:
        logo = await _fetch_institution_logo(
            institution_id, aspsp_country, enablebanking_service
        )
        if logo:
            enriched_account["logo"] = logo

    return enriched_account


def _extract_currency_from_balances(balances: dict[str, Any]) -> str | None:
    """Extract currency from the first balance in the balances data."""
    balances_list = balances.get("balances", [])
    if not balances_list:
        return None

    first_balance = balances_list[0]
    balance_amount = first_balance.get("balance_amount", {})
    return balance_amount.get("currency")


async def _fetch_institution_logo(
    aspsp_name: str, country: str, enablebanking_service: EnableBankingService
) -> str | None:
    """Fetch institution logo from EnableBanking API."""
    try:
        aspsps = await enablebanking_service.get_aspsps(country)
        for aspsp in aspsps:
            if aspsp.get("name") == aspsp_name:
                logo = aspsp.get("logo", "")
                if logo:
                    logger.info(f"Fetched logo for ASPSP {aspsp_name}: {logo}")
                return logo
        return None
    except Exception as e:
        logger.warning(f"Failed to fetch institution details for {aspsp_name}: {e}")
        return None


# --- Counterparty identity ---


def counterparty_name(raw_transaction: dict[str, Any], side: str) -> str:
    """Return the counterparty name from a raw EnableBanking transaction.

    EnableBanking nests these as `creditor: {name: ...}` / `debtor: {name: ...}`.
    Earlier code read flat `creditorName`/`debtorName` keys that the provider
    never sends, so every lookup silently returned "" — the flat form is still
    accepted here in case a provider or fixture uses it.
    """
    nested = raw_transaction.get(side)
    if isinstance(nested, dict):
        name = nested.get("name")
        if name:
            return str(name)
    return str(raw_transaction.get(f"{side}Name", "") or "")


# Noise that real bank descriptions wrap around the merchant name: card and
# terminal references, dates, and the payment-scheme prefixes used by the
# Portuguese and Revolut feeds this was measured against.
_MERCHANT_NOISE = re.compile(
    r"""
      \b\d{2}[-/]\d{2}(?:[-/]\d{2,4})?\b   # dates: 03-07, 12/03/24
    | \b[A-Z]{2}\d{18,}\b                   # IBANs embedded in transfer refs
    | \b[\d-]{6,}\b                         # reference numbers, incl. hyphenated
    | \b\d{4,}\b                            # terminal / card numbers
    | \bpending\b
    | \bcompras?\s+c?\.?\s*deb\b            # "COMPRA", "COMPRAS C.DEB"
    | \bpag\s+bxval\b
    | \bbx\s+valor\b
    | \b(?:trf|cobr)\s+sepa(?:\s+inst)?\b   # SEPA transfer/collection prefixes
    """,
    re.IGNORECASE | re.VERBOSE,
)


# Directional prefixes ("To …", "From …") describe the leg of a transfer, not
# who it was with, so they are stripped from the grouping key while staying in
# the display label.
_MERCHANT_KEY_PREFIX = re.compile(r"^(?:to|from|sent\s+to|paid\s+to)\s+", re.IGNORECASE)


def normalize_merchant(description: str) -> str:
    """Collapse a bank description down to a stable merchant label.

    Real remittance strings wrap the merchant in reference numbers, dates and
    scheme prefixes ("COMPRA 3007 Revolut 3600 Dublin IE"), so two charges from
    one merchant rarely share a description. Stripping that noise groups them.
    """
    cleaned = _MERCHANT_NOISE.sub(" ", description or "")
    # Punctuation carries no merchant identity but does vary between charges
    # ("Uber * Eats" vs "Uber   *eats").
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or (description or "").strip() or "Unknown"


def merchant_identity(
    raw_transaction: dict[str, Any], description: str, is_expense: bool
) -> tuple[str, str]:
    """Return (grouping_key, display_name) for a transaction's counterparty.

    Measured against real data, `creditor.name` is populated for only ~3.5% of
    transactions and `creditor_account.iban` only for transfers, so the
    description is the sole field present on every row and has to carry the
    grouping. The structured fields are preferred where they exist because they
    are already clean; otherwise the description is normalized.

    The sample database inverts these proportions (a generated `creditor.name`
    on ~97% of rows, a random IBAN per transaction), so it will flatter the
    structured path and hide how much work normalization is really doing.
    """
    side = "creditor" if is_expense else "debtor"
    name = counterparty_name(raw_transaction, side)
    # Some providers only populate the opposite side; take whatever is there
    # rather than falling straight through to the noisier description.
    if not name:
        name = counterparty_name(
            raw_transaction, "debtor" if is_expense else "creditor"
        )

    # Normalize whichever field we ended up with. Running the structured name
    # through the same pass matters: on real data the two disagree on wording
    # for the same merchant ("FLEXIBLE CASH FUNDS" vs "To Flexible Cash Funds"),
    # and keeping them separate splits one merchant into several.
    display = normalize_merchant(name or description)
    key = _MERCHANT_KEY_PREFIX.sub("", display.casefold()).strip()
    return key or display.casefold(), display


# --- Balance transformation ---


def merge_account_metadata_into_balances(
    balances: dict[str, Any],
    account_details: dict[str, Any],
) -> dict[str, Any]:
    """Merge account metadata into balance data for proper persistence."""
    balances_with_metadata = balances.copy()
    balances_with_metadata["institution_id"] = account_details.get("institution_id")
    balances_with_metadata["iban"] = account_details.get("iban")
    balances_with_metadata["account_status"] = account_details.get("status")
    return balances_with_metadata


def transform_to_database_format(
    account_id: str,
    balance_data: dict[str, Any],
) -> list[tuple[Any, ...]]:
    """Transform EnableBanking balance format to database row format."""
    rows = []

    for balance in balance_data.get("balances", []):
        balance_amount = balance.get("balance_amount", {})

        row = (
            account_id,
            balance_data.get("institution_id", "unknown"),
            balance_data.get("account_status"),
            balance_data.get("iban", "N/A"),
            float(balance_amount.get("amount", 0)),
            balance_amount.get("currency"),
            balance.get("balance_type"),
            datetime.now().isoformat(),
        )
        rows.append(row)

    return rows


# --- Transaction processing ---


def process_transactions(
    account_id: str,
    account_info: dict[str, Any],
    transaction_data: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    """Process raw transaction data into standardized format.

    Returns the processed transactions and the number that could not be
    consumed. A transaction the bank returns in a shape we cannot parse is
    skipped rather than raised, so one bad entry does not discard the whole
    account's batch; its raw payload is logged so it can be reported upstream.
    """
    transactions = []
    skipped = 0

    for transaction in transaction_data.get("transactions", []):
        status_raw = transaction.get("status", "BOOK")
        status = "booked" if status_raw == "BOOK" else "pending"
        try:
            processed = _process_single_transaction(
                account_id, account_info, transaction, status
            )
        except ValueError as e:
            skipped += 1
            logger.error(
                f"Skipping unparseable transaction for account {account_id}: "
                f"{describe_exception(e)}. Please report this upstream — anonymise "
                f"the payload below (IBANs, names, amounts) before sharing it. "
                f"Raw transaction: {transaction}"
            )
            continue
        transactions.append(processed)

    return transactions, skipped


def _process_single_transaction(
    account_id: str,
    account_info: dict[str, Any],
    transaction: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    """Process a single transaction into standardized format."""
    # Extract dates (EnableBanking uses snake_case). All three date fields are
    # optional in the EnableBanking schema and ASPSPs differ in which they
    # populate, so fall back across all of them rather than assuming the first
    # two are always present.
    candidates = []
    for field in ("booking_date", "value_date", "transaction_date"):
        raw_date = transaction.get(field)
        if not raw_date:
            continue
        try:
            candidates.append(datetime.fromisoformat(raw_date))
        except (TypeError, ValueError) as e:
            raise ValueError(f"Unparseable {field} {raw_date!r} in transaction") from e

    if not candidates:
        raise ValueError("No valid date found in transaction")

    # Earliest of the available dates, matching long-standing behaviour.
    min_date = min(candidates)

    # Extract amount and currency (EnableBanking uses snake_case)
    transaction_amount = transaction.get("transaction_amount", {})
    amount = float(transaction_amount.get("amount", 0))
    if transaction.get("credit_debit_indicator") == "DBIT":
        amount = -abs(amount)
    currency = transaction_amount.get("currency", "")

    # Extract description (EnableBanking returns remittance_information as list)
    remittance_info = transaction.get("remittance_information", [])
    if isinstance(remittance_info, list):
        description = ", ".join(remittance_info)
    else:
        description = str(remittance_info) if remittance_info else ""

    # Extract transaction IDs (EnableBanking uses snake_case)
    transaction_id = transaction.get("transaction_id")
    entry_reference = transaction.get("entry_reference")

    if not transaction_id:
        if entry_reference:
            transaction_id = entry_reference
        else:
            raise ValueError("Transaction missing required transaction_id field")

    return {
        "accountId": account_id,
        "transactionId": transaction_id,
        "internalTransactionId": entry_reference,
        "institutionId": account_info["institution_id"],
        "iban": account_info.get("iban", "N/A"),
        # Stored as an ISO 8601 T-separated string; passing a datetime would go
        # through sqlite3's deprecated (and space-separated) datetime adapter.
        "transactionDate": min_date.isoformat(),
        "description": description,
        "transactionValue": amount,
        "transactionCurrency": currency,
        "transactionStatus": status,
        "rawTransaction": transaction,
    }
