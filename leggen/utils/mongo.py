import click
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from leggen.utils.text import success, warning


def save_transactions(ctx: click.Context, account: str, transactions: list):
    # Connect to MongoDB
    mongo_uri = ctx.obj["mongo_uri"]
    client = MongoClient(mongo_uri)
    db = client["leggen"]
    transactions_collection = db["transactions"]

    # Create a unique index on internalTransactionId
    transactions_collection.create_index("internalTransactionId", unique=True)

    # Insert transactions into MongoDB
    new_transactions_count = 0
    duplicates_count = 0

    for transaction in transactions:
        try:
            transactions_collection.insert_one(transaction)
            new_transactions_count += 1
        except DuplicateKeyError:
            # A transaction with the same ID already exists, skip insertion
            duplicates_count += 1

    success(f"[{account}] Inserted {new_transactions_count} new transactions")
    if duplicates_count:
        warning(f"[{account}] Skipped {duplicates_count} duplicate transactions")
