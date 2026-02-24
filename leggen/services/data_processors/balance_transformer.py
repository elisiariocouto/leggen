"""Balance data transformation processor for format conversions."""

from datetime import datetime
from typing import Any, Dict, List, Tuple


class BalanceTransformer:
    """Transforms balance data between EnableBanking and internal database formats."""

    def merge_account_metadata_into_balances(
        self,
        balances: Dict[str, Any],
        account_details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Merge account metadata into balance data for proper persistence.

        This adds institution_id, iban, and account_status to the balances
        so they can be persisted alongside the balance data.

        Args:
            balances: Raw balance data from EnableBanking
            account_details: Enriched account details containing metadata

        Returns:
            Balance data with account metadata merged in
        """
        balances_with_metadata = balances.copy()
        balances_with_metadata["institution_id"] = account_details.get("institution_id")
        balances_with_metadata["iban"] = account_details.get("iban")
        balances_with_metadata["account_status"] = account_details.get("status")
        return balances_with_metadata

    def transform_to_database_format(
        self,
        account_id: str,
        balance_data: Dict[str, Any],
    ) -> List[Tuple[Any, ...]]:
        """
        Transform EnableBanking balance format to database row format.

        Converts nested EnableBanking balance structure into flat tuples
        ready for SQLite insertion.

        Args:
            account_id: The account ID
            balance_data: Balance data with merged account metadata

        Returns:
            List of tuples in database row format (account_id, bank, status, ...)
        """
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
