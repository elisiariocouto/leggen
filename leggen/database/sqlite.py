import json
import sqlite3
from sqlite3 import IntegrityError

import click

from leggen.utils.text import success, warning
from leggen.utils.paths import path_manager


def persist_balances(ctx: click.Context, balance: dict):
    # Connect to SQLite database
    db_path = path_manager.get_database_path()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create the accounts table if it doesn't exist
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS accounts (
        id TEXT PRIMARY KEY,
        institution_id TEXT,
        status TEXT,
        iban TEXT,
        name TEXT,
        currency TEXT,
        created DATETIME,
        last_accessed DATETIME,
        last_updated DATETIME
    )"""
    )

    # Create indexes for accounts table
    cursor.execute(
        """CREATE INDEX IF NOT EXISTS idx_accounts_institution_id
           ON accounts(institution_id)"""
    )
    cursor.execute(
        """CREATE INDEX IF NOT EXISTS idx_accounts_status
           ON accounts(status)"""
    )

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

    # Insert balance into SQLite database
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
                balance["account_id"],
                balance["bank"],
                balance["status"],
                balance["iban"],
                balance["amount"],
                balance["currency"],
                balance["type"],
                balance["timestamp"],
            ),
        )
    except IntegrityError:
        warning(f"[{balance['account_id']}] Skipped duplicate balance")

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    success(f"[{balance['account_id']}] Inserted balance of type {balance['type']}")

    return balance


def persist_transactions(ctx: click.Context, account: str, transactions: list) -> list:
    # Connect to SQLite database
    db_path = path_manager.get_database_path()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create the transactions table if it doesn't exist
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS transactions (
        accountId TEXT NOT NULL,
        transactionId TEXT NOT NULL,
        internalTransactionId TEXT,
        institutionId TEXT,
        iban TEXT,
        transactionDate DATETIME,
        description TEXT,
        transactionValue REAL,
        transactionCurrency TEXT,
        transactionStatus TEXT,
        rawTransaction JSON,
        PRIMARY KEY (accountId, transactionId)
    )"""
    )

    # Create indexes for better performance
    cursor.execute(
        """CREATE INDEX IF NOT EXISTS idx_transactions_internal_id
           ON transactions(internalTransactionId)"""
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

    # Insert transactions into SQLite database
    duplicates_count = 0

    # Prepare an SQL statement for inserting data
    insert_sql = """INSERT OR REPLACE INTO transactions (
        accountId,
        transactionId,
        internalTransactionId,
        institutionId,
        iban,
        transactionDate,
        description,
        transactionValue,
        transactionCurrency,
        transactionStatus,
        rawTransaction
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

    new_transactions = []

    for transaction in transactions:
        try:
            cursor.execute(
                insert_sql,
                (
                    transaction["accountId"],
                    transaction["transactionId"],
                    transaction.get("internalTransactionId"),
                    transaction["institutionId"],
                    transaction["iban"],
                    transaction["transactionDate"],
                    transaction["description"],
                    transaction["transactionValue"],
                    transaction["transactionCurrency"],
                    transaction["transactionStatus"],
                    json.dumps(transaction["rawTransaction"]),
                ),
            )
            new_transactions.append(transaction)
        except IntegrityError:
            # A transaction with the same ID already exists, indicating a duplicate
            duplicates_count += 1

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    success(f"[{account}] Inserted {len(new_transactions)} new transactions")
    if duplicates_count:
        warning(f"[{account}] Skipped {duplicates_count} duplicate transactions")

    return new_transactions


def get_transactions(
    account_id=None,
    limit=100,
    offset=0,
    date_from=None,
    date_to=None,
    min_amount=None,
    max_amount=None,
    search=None,
):
    """Get transactions from SQLite database with optional filtering"""
    db_path = path_manager.get_database_path()
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    cursor = conn.cursor()

    # Build query with filters
    query = "SELECT * FROM transactions WHERE 1=1"
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

    if min_amount is not None:
        query += " AND transactionValue >= ?"
        params.append(min_amount)

    if max_amount is not None:
        query += " AND transactionValue <= ?"
        params.append(max_amount)

    if search:
        query += " AND description LIKE ?"
        params.append(f"%{search}%")

    # Add ordering and pagination
    query += " ORDER BY transactionDate DESC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    if offset:
        query += " OFFSET ?"
        params.append(offset)

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to list of dicts and parse JSON fields
        transactions = []
        for row in rows:
            transaction = dict(row)
            if transaction["rawTransaction"]:
                transaction["rawTransaction"] = json.loads(
                    transaction["rawTransaction"]
                )
            transactions.append(transaction)

        conn.close()
        return transactions

    except Exception as e:
        conn.close()
        raise e


def get_balances(account_id=None):
    """Get latest balances from SQLite database"""
    db_path = path_manager.get_database_path()
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get latest balance for each account_id and type combination
    query = """
        SELECT * FROM balances b1
        WHERE b1.timestamp = (
            SELECT MAX(b2.timestamp)
            FROM balances b2
            WHERE b2.account_id = b1.account_id AND b2.type = b1.type
        )
    """
    params = []

    if account_id:
        query += " AND b1.account_id = ?"
        params.append(account_id)

    query += " ORDER BY b1.account_id, b1.type"

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()

        balances = [dict(row) for row in rows]
        conn.close()
        return balances

    except Exception as e:
        conn.close()
        raise e


def get_account_summary(account_id):
    """Get basic account info from transactions table (avoids GoCardless API call)"""
    db_path = path_manager.get_database_path()
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get account info from most recent transaction
        cursor.execute(
            """
            SELECT DISTINCT accountId, institutionId, iban
            FROM transactions
            WHERE accountId = ?
            ORDER BY transactionDate DESC
            LIMIT 1
        """,
            (account_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    except Exception as e:
        conn.close()
        raise e


def get_transaction_count(account_id=None, **filters):
    """Get total count of transactions matching filters"""
    db_path = path_manager.get_database_path()
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    query = "SELECT COUNT(*) FROM transactions WHERE 1=1"
    params = []

    if account_id:
        query += " AND accountId = ?"
        params.append(account_id)

    # Add same filters as get_transactions
    if filters.get("date_from"):
        query += " AND transactionDate >= ?"
        params.append(filters["date_from"])

    if filters.get("date_to"):
        query += " AND transactionDate <= ?"
        params.append(filters["date_to"])

    if filters.get("min_amount") is not None:
        query += " AND transactionValue >= ?"
        params.append(filters["min_amount"])

    if filters.get("max_amount") is not None:
        query += " AND transactionValue <= ?"
        params.append(filters["max_amount"])

    if filters.get("search"):
        query += " AND description LIKE ?"
        params.append(f"%{filters['search']}%")

    try:
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        conn.close()
        return count

    except Exception as e:
        conn.close()
        raise e


def persist_account(account_data: dict):
    """Persist account details to SQLite database"""
    db_path = path_manager.get_database_path()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create the accounts table if it doesn't exist
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS accounts (
        id TEXT PRIMARY KEY,
        institution_id TEXT,
        status TEXT,
        iban TEXT,
        name TEXT,
        currency TEXT,
        created DATETIME,
        last_accessed DATETIME,
        last_updated DATETIME
    )"""
    )

    # Create indexes for accounts table
    cursor.execute(
        """CREATE INDEX IF NOT EXISTS idx_accounts_institution_id
           ON accounts(institution_id)"""
    )
    cursor.execute(
        """CREATE INDEX IF NOT EXISTS idx_accounts_status
           ON accounts(status)"""
    )

    try:
        # Insert or replace account data
        cursor.execute(
            """INSERT OR REPLACE INTO accounts (
            id,
            institution_id,
            status,
            iban,
            name,
            currency,
            created,
            last_accessed,
            last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                account_data["id"],
                account_data["institution_id"],
                account_data["status"],
                account_data.get("iban"),
                account_data.get("name"),
                account_data.get("currency"),
                account_data["created"],
                account_data.get("last_accessed"),
                account_data.get("last_updated", account_data["created"]),
            ),
        )
        conn.commit()
        conn.close()

        success(f"[{account_data['id']}] Account details persisted to database")
        return account_data

    except Exception as e:
        conn.close()
        raise e


def get_accounts(account_ids=None):
    """Get account details from SQLite database"""
    db_path = path_manager.get_database_path()
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM accounts"
    params = []

    if account_ids:
        placeholders = ",".join("?" * len(account_ids))
        query += f" WHERE id IN ({placeholders})"
        params.extend(account_ids)

    query += " ORDER BY created DESC"

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()

        accounts = [dict(row) for row in rows]
        conn.close()
        return accounts

    except Exception as e:
        conn.close()
        raise e


def get_account(account_id: str):
    """Get specific account details from SQLite database"""
    db_path = path_manager.get_database_path()
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    except Exception as e:
        conn.close()
        raise e
