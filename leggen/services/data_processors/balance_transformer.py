"""Balance data transformation functions for format conversions."""

from datetime import datetime
from typing import Any, Dict, List, Tuple


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
