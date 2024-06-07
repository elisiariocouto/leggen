import json
import sqlite3
from sqlite3 import IntegrityError

import click

from leggen.utils.text import success, warning


def persist_balances(ctx: click.Context, balance: dict):
    # Connect to SQLite database
    conn = sqlite3.connect("./leggen.db")
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
    conn = sqlite3.connect("./leggen.db")
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

    # Insert transactions into SQLite database
    duplicates_count = 0

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
