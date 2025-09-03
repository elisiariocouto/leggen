from datetime import datetime
from typing import List, Dict, Any, Optional

from loguru import logger

from leggend.config import config
import leggen.database.sqlite as sqlite_db


class DatabaseService:
    def __init__(self):
        self.db_config = config.database_config
        self.sqlite_enabled = self.db_config.get("sqlite", True)

    async def persist_balance(
        self, account_id: str, balance_data: Dict[str, Any]
    ) -> None:
        """Persist account balance data"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, skipping balance persistence")
            return

        await self._persist_balance_sqlite(account_id, balance_data)

    async def persist_transactions(
        self, account_id: str, transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Persist transactions and return new transactions"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, skipping transaction persistence")
            return transactions

        return await self._persist_transactions_sqlite(account_id, transactions)

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

    async def get_transactions_from_db(
        self,
        account_id: Optional[str] = None,
        limit: Optional[int] = 100,
        offset: Optional[int] = 0,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get transactions from SQLite database"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot read transactions")
            return []

        try:
            transactions = sqlite_db.get_transactions(
                account_id=account_id,
                limit=limit,
                offset=offset,
                date_from=date_from,
                date_to=date_to,
                min_amount=min_amount,
                max_amount=max_amount,
                search=search,
            )
            logger.debug(f"Retrieved {len(transactions)} transactions from database")
            return transactions
        except Exception as e:
            logger.error(f"Failed to get transactions from database: {e}")
            return []

    async def get_transaction_count_from_db(
        self,
        account_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        search: Optional[str] = None,
    ) -> int:
        """Get total count of transactions from SQLite database"""
        if not self.sqlite_enabled:
            return 0

        try:
            filters = {
                "date_from": date_from,
                "date_to": date_to,
                "min_amount": min_amount,
                "max_amount": max_amount,
                "search": search,
            }
            # Remove None values
            filters = {k: v for k, v in filters.items() if v is not None}

            count = sqlite_db.get_transaction_count(account_id=account_id, **filters)
            logger.debug(f"Total transaction count: {count}")
            return count
        except Exception as e:
            logger.error(f"Failed to get transaction count from database: {e}")
            return 0

    async def get_balances_from_db(
        self, account_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get balances from SQLite database"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot read balances")
            return []

        try:
            balances = sqlite_db.get_balances(account_id=account_id)
            logger.debug(f"Retrieved {len(balances)} balances from database")
            return balances
        except Exception as e:
            logger.error(f"Failed to get balances from database: {e}")
            return []

    async def get_account_summary_from_db(
        self, account_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get basic account info from SQLite database (avoids GoCardless call)"""
        if not self.sqlite_enabled:
            return None

        try:
            summary = sqlite_db.get_account_summary(account_id)
            if summary:
                logger.debug(
                    f"Retrieved account summary from database for {account_id}"
                )
            return summary
        except Exception as e:
            logger.error(f"Failed to get account summary from database: {e}")
            return None

    async def _persist_balance_sqlite(
        self, account_id: str, balance_data: Dict[str, Any]
    ) -> None:
        """Persist balance to SQLite"""
        try:
            import sqlite3

            from pathlib import Path

            db_path = Path.home() / ".config" / "leggen" / "leggen.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Create the balances table if it doesn't exist
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT,
                bank TEXT,
                status TEXT,
                iban TEXT,
                amount REAL,
                currency TEXT,
                type TEXT,
                timestamp DATETIME
            )"""
            )

            # Create indexes for better performance
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_balances_account_id
                   ON balances(account_id)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_balances_timestamp
                   ON balances(timestamp)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_balances_account_type_timestamp
                   ON balances(account_id, type, timestamp)"""
            )

            # Convert GoCardless balance format to our format and persist
            for balance in balance_data.get("balances", []):
                balance_amount = balance["balanceAmount"]

                try:
                    cursor.execute(
                        """INSERT INTO balances (
                        account_id,
                        bank,
                        status,
                        iban,
                        amount,
                        currency,
                        type,
                        timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            account_id,
                            balance_data.get("institution_id", "unknown"),
                            "active",
                            balance_data.get("iban", "N/A"),
                            float(balance_amount["amount"]),
                            balance_amount["currency"],
                            balance["balanceType"],
                            datetime.now(),
                        ),
                    )
                except sqlite3.IntegrityError:
                    logger.warning(f"Skipped duplicate balance for {account_id}")

            conn.commit()
            conn.close()

            logger.info(f"Persisted balances to SQLite for account {account_id}")
        except Exception as e:
            logger.error(f"Failed to persist balances to SQLite: {e}")
            raise

    async def _persist_transactions_sqlite(
        self, account_id: str, transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Persist transactions to SQLite"""
        try:
            import sqlite3
            import json

            from pathlib import Path

            db_path = Path.home() / ".config" / "leggen" / "leggen.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Create the transactions table if it doesn't exist
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS transactions (
                internalTransactionId TEXT PRIMARY KEY,
                institutionId TEXT,
                iban TEXT,
                transactionDate DATETIME,
                description TEXT,
                transactionValue REAL,
                transactionCurrency TEXT,
                transactionStatus TEXT,
                accountId TEXT,
                rawTransaction JSON
            )"""
            )

            # Create indexes for better performance
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_transactions_account_id
                   ON transactions(accountId)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_transactions_date
                   ON transactions(transactionDate)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_transactions_account_date
                   ON transactions(accountId, transactionDate)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_transactions_amount
                   ON transactions(transactionValue)"""
            )

            # Prepare an SQL statement for inserting data
            insert_sql = """INSERT INTO transactions (
                internalTransactionId,
                institutionId,
                iban,
                transactionDate,
                description,
                transactionValue,
                transactionCurrency,
                transactionStatus,
                accountId,
                rawTransaction
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

            new_transactions = []

            for transaction in transactions:
                try:
                    cursor.execute(
                        insert_sql,
                        (
                            transaction["internalTransactionId"],
                            transaction["institutionId"],
                            transaction["iban"],
                            transaction["transactionDate"],
                            transaction["description"],
                            transaction["transactionValue"],
                            transaction["transactionCurrency"],
                            transaction["transactionStatus"],
                            transaction["accountId"],
                            json.dumps(transaction["rawTransaction"]),
                        ),
                    )
                    new_transactions.append(transaction)
                except sqlite3.IntegrityError:
                    # Transaction already exists
                    continue

            conn.commit()
            conn.close()

            logger.info(
                f"Persisted {len(new_transactions)} new transactions to SQLite for account {account_id}"
            )
            return new_transactions
        except Exception as e:
            logger.error(f"Failed to persist transactions to SQLite: {e}")
            raise
