import click
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from leggen.utils.text import success, warning


def persist_transactions(ctx: click.Context, account: str, transactions: list) -> list:
    # Connect to MongoDB
    mongo_uri = ctx.obj.get("database", {}).get("mongodb", {}).get("uri")
    client = MongoClient(mongo_uri)
    db = client["leggen"]
    transactions_collection = db["transactions"]

    # Create a unique index on internalTransactionId
    transactions_collection.create_index("internalTransactionId", unique=True)

    # Insert transactions into MongoDB
    duplicates_count = 0

    new_transactions = []

    for transaction in transactions:
        try:
            transactions_collection.insert_one(transaction)
            new_transactions.append(transaction)
        except DuplicateKeyError:
            # A transaction with the same ID already exists, skip insertion
            duplicates_count += 1

    success(f"[{account}] Inserted {len(new_transactions)} new transactions")
    if duplicates_count:
        warning(f"[{account}] Skipped {duplicates_count} duplicate transactions")

    return new_transactions
