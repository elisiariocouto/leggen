import click
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from leggen.notifications.discord import send_message
from leggen.utils.text import success, warning


def save_transactions(ctx: click.Context, account: str, transactions: list):
    # Connect to MongoDB
    mongo_uri = ctx.obj.get("database", {}).get("mongodb", {}).get("uri")
    client = MongoClient(mongo_uri)
    db = client["leggen"]
    transactions_collection = db["transactions"]

    # Create a unique index on internalTransactionId
    transactions_collection.create_index("internalTransactionId", unique=True)

    # Insert transactions into MongoDB
    new_transactions_count = 0
    duplicates_count = 0

    notification_transactions = []
    filters_case_insensitive = {}
    if ctx.obj.get("filters", {}).get("enabled", False):
        filters_case_insensitive = ctx.obj.get("filters", {}).get(
            "case-insensitive", {}
        )

    for transaction in transactions:
        try:
            transactions_collection.insert_one(transaction)
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

        except DuplicateKeyError:
            # A transaction with the same ID already exists, skip insertion
            duplicates_count += 1

    # Send a notification with the transactions that match the filters
    if notification_transactions:
        send_message(ctx, notification_transactions)

    success(f"[{account}] Inserted {new_transactions_count} new transactions")
    if duplicates_count:
        warning(f"[{account}] Skipped {duplicates_count} duplicate transactions")
