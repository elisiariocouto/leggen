import json
import sqlite3
from sqlite3 import IntegrityError

import click

from leggen.notifications.discord import send_message
from leggen.utils.text import success, warning


def save_transactions(ctx: click.Context, account: str, transactions: list):
    # Path to your SQLite database file

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
    new_transactions_count = 0
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

    notification_transactions = []
    filters_case_insensitive = {}
    if ctx.obj.get("filters", {}).get("enabled", False):
        filters_case_insensitive = ctx.obj.get("filters", {}).get(
            "case-insensitive", {}
        )

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
            new_transactions_count += 1

            # Add transaction to the list of transactions to be sent as a notification
            for _, v in filters_case_insensitive.items():
                if v.lower() in transaction["description"].lower():
                    notification_transactions.append(
                        {
                            "name": transaction["description"],
                            "value": transaction["transactionValue"],
                            "currency": transaction["transactionCurrency"],
                            "date": transaction["transactionDate"],
                        }
                    )
        except IntegrityError:
            # A transaction with the same ID already exists, indicating a duplicate
            duplicates_count += 1

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    # Send a notification with the transactions that match the filters
    if notification_transactions:
        send_message(ctx, notification_transactions)

    success(f"[{account}] Inserted {new_transactions_count} new transactions")
    if duplicates_count:
        warning(f"[{account}] Skipped {duplicates_count} duplicate transactions")
