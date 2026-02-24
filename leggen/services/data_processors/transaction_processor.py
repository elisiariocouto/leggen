from datetime import datetime
from typing import Any, Dict, List

from loguru import logger


class TransactionProcessor:
    """Handles processing and transformation of raw transaction data"""

    def process_transactions(
        self,
        account_id: str,
        account_info: Dict[str, Any],
        transaction_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Process raw transaction data into standardized format"""
        transactions = []
        logger.debug(transaction_data)

        for transaction in transaction_data.get("transactions", []):
            status_raw = transaction.get("status", "BOOK")
            status = "booked" if status_raw == "BOOK" else "pending"
            processed = self._process_single_transaction(
                account_id, account_info, transaction, status
            )
            transactions.append(processed)

        return transactions

    def _process_single_transaction(
        self,
        account_id: str,
        account_info: Dict[str, Any],
        transaction: Dict[str, Any],
        status: str,
    ) -> Dict[str, Any]:
        """Process a single transaction into standardized format"""
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
