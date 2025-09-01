from datetime import datetime
from typing import List, Dict, Any, Optional

from loguru import logger

from leggend.config import config


class DatabaseService:
    def __init__(self):
        self.db_config = config.database_config
        self.sqlite_enabled = self.db_config.get("sqlite", False)
        self.mongodb_enabled = self.db_config.get("mongodb", False)

    async def persist_balance(self, account_id: str, balance_data: Dict[str, Any]) -> None:
        """Persist account balance data"""
        if not self.sqlite_enabled and not self.mongodb_enabled:
            logger.warning("No database engine enabled, skipping balance persistence")
            return

        if self.sqlite_enabled:
            await self._persist_balance_sqlite(account_id, balance_data)
        
        if self.mongodb_enabled:
            await self._persist_balance_mongodb(account_id, balance_data)

    async def persist_transactions(self, account_id: str, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Persist transactions and return new transactions"""
        if not self.sqlite_enabled and not self.mongodb_enabled:
            logger.warning("No database engine enabled, skipping transaction persistence")
            return transactions

        if self.sqlite_enabled:
            return await self._persist_transactions_sqlite(account_id, transactions)
        elif self.mongodb_enabled:
            return await self._persist_transactions_mongodb(account_id, transactions)

        return []

    def process_transactions(self, account_id: str, account_info: Dict[str, Any], transaction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process raw transaction data into standardized format"""
        transactions = []
        
        # Process booked transactions
        for transaction in transaction_data.get("transactions", {}).get("booked", []):
            processed = self._process_single_transaction(account_id, account_info, transaction, "booked")
            transactions.append(processed)

        # Process pending transactions  
        for transaction in transaction_data.get("transactions", {}).get("pending", []):
            processed = self._process_single_transaction(account_id, account_info, transaction, "pending")
            transactions.append(processed)

        return transactions

    def _process_single_transaction(self, account_id: str, account_info: Dict[str, Any], transaction: Dict[str, Any], status: str) -> Dict[str, Any]:
        """Process a single transaction into standardized format"""
        # Extract dates
        booked_date = transaction.get("bookingDateTime") or transaction.get("bookingDate")
        value_date = transaction.get("valueDateTime") or transaction.get("valueDate")
        
        if booked_date and value_date:
            min_date = min(
                datetime.fromisoformat(booked_date), 
                datetime.fromisoformat(value_date)
            )
        else:
            min_date = datetime.fromisoformat(booked_date or value_date)

        # Extract amount and currency
        transaction_amount = transaction.get("transactionAmount", {})
        amount = float(transaction_amount.get("amount", 0))
        currency = transaction_amount.get("currency", "")

        # Extract description
        description = transaction.get(
            "remittanceInformationUnstructured",
            ",".join(transaction.get("remittanceInformationUnstructuredArray", []))
        )

        return {
            "internalTransactionId": transaction.get("internalTransactionId"),
            "institutionId": account_info["institution_id"],
            "iban": account_info.get("iban", "N/A"),
            "transactionDate": min_date,
            "description": description,
            "transactionValue": amount,
            "transactionCurrency": currency,
            "transactionStatus": status,
            "accountId": account_id,
            "rawTransaction": transaction,
        }

    async def _persist_balance_sqlite(self, account_id: str, balance_data: Dict[str, Any]) -> None:
        """Persist balance to SQLite - placeholder implementation"""
        # Would import and use leggen.database.sqlite
        logger.info(f"Persisting balance to SQLite for account {account_id}")

    async def _persist_balance_mongodb(self, account_id: str, balance_data: Dict[str, Any]) -> None:
        """Persist balance to MongoDB - placeholder implementation"""
        # Would import and use leggen.database.mongo
        logger.info(f"Persisting balance to MongoDB for account {account_id}")

    async def _persist_transactions_sqlite(self, account_id: str, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Persist transactions to SQLite - placeholder implementation"""
        # Would import and use leggen.database.sqlite
        logger.info(f"Persisting {len(transactions)} transactions to SQLite for account {account_id}")
        return transactions  # Return new transactions for notifications

    async def _persist_transactions_mongodb(self, account_id: str, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Persist transactions to MongoDB - placeholder implementation"""
        # Would import and use leggen.database.mongo  
        logger.info(f"Persisting {len(transactions)} transactions to MongoDB for account {account_id}")
        return transactions  # Return new transactions for notifications