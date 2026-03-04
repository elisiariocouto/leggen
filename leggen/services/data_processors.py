"""Data processing layer for all transformation logic."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from leggen.services.enablebanking_service import EnableBankingService

# --- Account enrichment ---


async def enrich_account_details(
    account_details: Dict[str, Any],
    balances: Dict[str, Any],
    aspsp_country: str | None = None,
    enablebanking_service: EnableBankingService | None = None,
) -> Dict[str, Any]:
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


def _extract_currency_from_balances(balances: Dict[str, Any]) -> str | None:
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


# --- Analytics ---


def calculate_historical_balances(
    db_path: Path,
    account_id: Optional[str] = None,
    days: int = 365,
) -> List[Dict[str, Any]]:
    """
    Generate historical balance progression based on transaction history.

    Uses current balances and subtracts future transactions to calculate
    balance at each historical point in time.

    Args:
        db_path: Path to SQLite database
        account_id: Optional account ID to filter by
        days: Number of days to look back (default 365)

    Returns:
        List of historical balance data points
    """
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        today_date = datetime.now().date().isoformat()

        # Single SQL query to generate historical balances using window functions
        query = """
        WITH RECURSIVE date_series AS (
            -- Generate weekly dates from cutoff_date to today
            SELECT date(?) as ref_date
            UNION ALL
            SELECT date(ref_date, '+7 days')
            FROM date_series
            WHERE ref_date < date(?)
        ),
        current_balances AS (
            -- Get current balance for each account/type
            SELECT account_id, type, amount, currency
            FROM balances b1
            WHERE b1.timestamp = (
                SELECT MAX(b2.timestamp)
                FROM balances b2
                WHERE b2.account_id = b1.account_id AND b2.type = b1.type
            )
            {account_filter}
            AND b1.type = 'closingBooked'  -- Focus on closingBooked for charts
        ),
        historical_points AS (
            -- Calculate balance at each weekly point by subtracting future transactions
            SELECT
                cb.account_id,
                cb.type as balance_type,
                cb.currency,
                ds.ref_date,
                cb.amount - COALESCE(
                    (SELECT SUM(t.transactionValue)
                     FROM transactions t
                     WHERE t.accountId = cb.account_id
                     AND date(t.transactionDate) > ds.ref_date), 0
                ) as balance_amount
            FROM current_balances cb
            CROSS JOIN date_series ds
        )
        SELECT
            account_id || '_' || balance_type || '_' || ref_date as id,
            account_id,
            balance_amount,
            balance_type,
            currency,
            ref_date as reference_date
        FROM historical_points
        ORDER BY account_id, ref_date
        """

        # Build parameters and account filter
        params = [cutoff_date, today_date]
        if account_id:
            account_filter = "AND b1.account_id = ?"
            params.append(account_id)
        else:
            account_filter = ""

        # Format the query with conditional filter
        formatted_query = query.format(account_filter=account_filter)

        cursor.execute(formatted_query, params)
        rows = cursor.fetchall()

        conn.close()
        return [dict(row) for row in rows]

    except Exception as e:
        conn.close()
        logger.error(f"Failed to calculate historical balances: {e}")
        raise


def calculate_monthly_stats(
    db_path: Path,
    account_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Calculate monthly transaction statistics aggregated from database.

    Sums transactions by month and calculates income, expenses, and net values.

    Args:
        db_path: Path to SQLite database
        account_id: Optional account ID to filter by
        date_from: Optional start date (ISO format)
        date_to: Optional end date (ISO format)

    Returns:
        List of monthly statistics with income, expenses, and net totals
    """
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # SQL query to aggregate transactions by month
        query = """
        SELECT
            strftime('%Y-%m', transactionDate) as month,
            COALESCE(SUM(CASE WHEN transactionValue > 0 THEN transactionValue ELSE 0 END), 0) as income,
            COALESCE(SUM(CASE WHEN transactionValue < 0 THEN ABS(transactionValue) ELSE 0 END), 0) as expenses,
            COALESCE(SUM(transactionValue), 0) as net
        FROM transactions
        WHERE 1=1
        """

        params = []

        if account_id:
            query += " AND accountId = ?"
            params.append(account_id)

        if date_from:
            query += " AND transactionDate >= ?"
            params.append(date_from)

        if date_to:
            query += " AND transactionDate <= ?"
            params.append(date_to)

        query += """
        GROUP BY strftime('%Y-%m', transactionDate)
        ORDER BY month ASC
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to desired format with proper month display
        monthly_stats = []
        for row in rows:
            # Convert YYYY-MM to display format like "Mar 2024"
            year, month_num = row["month"].split("-")
            month_date = datetime.strptime(f"{year}-{month_num}-01", "%Y-%m-%d")
            display_month = month_date.strftime("%b %Y")

            monthly_stats.append(
                {
                    "month": display_month,
                    "income": round(row["income"], 2),
                    "expenses": round(row["expenses"], 2),
                    "net": round(row["net"], 2),
                }
            )

        conn.close()
        return monthly_stats

    except Exception as e:
        conn.close()
        logger.error(f"Failed to calculate monthly stats: {e}")
        raise


# --- Balance transformation ---


def merge_account_metadata_into_balances(
    balances: Dict[str, Any],
    account_details: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge account metadata into balance data for proper persistence."""
    balances_with_metadata = balances.copy()
    balances_with_metadata["institution_id"] = account_details.get("institution_id")
    balances_with_metadata["iban"] = account_details.get("iban")
    balances_with_metadata["account_status"] = account_details.get("status")
    return balances_with_metadata


def transform_to_database_format(
    account_id: str,
    balance_data: Dict[str, Any],
) -> List[Tuple[Any, ...]]:
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
    account_info: Dict[str, Any],
    transaction_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Process raw transaction data into standardized format."""
    transactions = []
    logger.debug(transaction_data)

    for transaction in transaction_data.get("transactions", []):
        status_raw = transaction.get("status", "BOOK")
        status = "booked" if status_raw == "BOOK" else "pending"
        processed = _process_single_transaction(
            account_id, account_info, transaction, status
        )
        transactions.append(processed)

    return transactions


def _process_single_transaction(
    account_id: str,
    account_info: Dict[str, Any],
    transaction: Dict[str, Any],
    status: str,
) -> Dict[str, Any]:
    """Process a single transaction into standardized format."""
    # Extract dates (EnableBanking uses snake_case)
    booked_date = transaction.get("booking_date")
    value_date = transaction.get("value_date")

    if booked_date and value_date:
        min_date = min(
            datetime.fromisoformat(booked_date), datetime.fromisoformat(value_date)
        )
    else:
        date_str = booked_date or value_date
        if not date_str:
            raise ValueError("No valid date found in transaction")
        min_date = datetime.fromisoformat(date_str)

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
        "transactionDate": min_date,
        "description": description,
        "transactionValue": amount,
        "transactionCurrency": currency,
        "transactionStatus": status,
        "rawTransaction": transaction,
    }
