from datetime import datetime
from typing import Any, Dict, List


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

        # Process booked transactions
        for transaction in transaction_data.get("transactions", {}).get("booked", []):
            processed = self._process_single_transaction(
                account_id, account_info, transaction, "booked"
            )
            transactions.append(processed)

        # Process pending transactions
        for transaction in transaction_data.get("transactions", {}).get("pending", []):
            processed = self._process_single_transaction(
                account_id, account_info, transaction, "pending"
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
        # Extract dates
        booked_date = transaction.get("bookingDateTime") or transaction.get(
            "bookingDate"
        )
        value_date = transaction.get("valueDateTime") or transaction.get("valueDate")

        if booked_date and value_date:
            min_date = min(
                datetime.fromisoformat(booked_date), datetime.fromisoformat(value_date)
            )
        else:
            date_str = booked_date or value_date
            if not date_str:
                raise ValueError("No valid date found in transaction")
            min_date = datetime.fromisoformat(date_str)

        # Extract amount and currency
        transaction_amount = transaction.get("transactionAmount", {})
        amount = float(transaction_amount.get("amount", 0))
        currency = transaction_amount.get("currency", "")

        # Extract description
        description = transaction.get(
            "remittanceInformationUnstructured",
            ",".join(transaction.get("remittanceInformationUnstructuredArray", [])),
        )

        # Extract transaction IDs - transactionId is now primary, internalTransactionId is reference
        transaction_id = transaction.get("transactionId")
        internal_transaction_id = transaction.get("internalTransactionId")

        if not transaction_id:
            raise ValueError("Transaction missing required transactionId field")

        return {
            "accountId": account_id,
            "transactionId": transaction_id,
            "internalTransactionId": internal_transaction_id,
            "institutionId": account_info["institution_id"],
            "iban": account_info.get("iban", "N/A"),
            "transactionDate": min_date,
            "description": description,
            "transactionValue": amount,
            "transactionCurrency": currency,
            "transactionStatus": status,
            "rawTransaction": transaction,
        }
