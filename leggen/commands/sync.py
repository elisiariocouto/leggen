import click
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from leggen.main import cli
from leggen.utils.network import get
from leggen.utils.text import error, info, success, warning


def save_transactions(ctx: click.Context, account: str):
    info(f"[{account}] Getting transactions")
    all_transactions = []
    account_transactions = get(ctx, f"/accounts/{account}/transactions/").get(
        "transactions", []
    )

    for transaction in account_transactions.get("booked", []):
        transaction["accountId"] = account
        transaction["transactionStatus"] = "booked"
        all_transactions.append(transaction)

    for transaction in account_transactions.get("pending", []):
        transaction["accountId"] = account
        transaction["transactionStatus"] = "pending"
        all_transactions.append(transaction)

    info(f"[{account}] Fetched {len(all_transactions)} transactions, saving to MongoDB")

    # Connect to MongoDB
    mongo_uri = ctx.obj["mongo_uri"]
    client = MongoClient(mongo_uri)
    db = client["leggen"]
    transactions_collection = db["transactions"]

    # Create a unique index on transactionId
    transactions_collection.create_index("transactionId", unique=True)

    # Insert transactions into MongoDB
    new_transactions_count = 0
    duplicates_count = 0

    for transaction in all_transactions:
        try:
            transactions_collection.insert_one(transaction)
            new_transactions_count += 1
        except DuplicateKeyError:
            # A transaction with the same ID already exists, skip insertion
            duplicates_count += 1

    success(f"[{account}] Inserted {new_transactions_count} new transactions")
    if duplicates_count:
        warning(f"[{account}] Skipped {duplicates_count} duplicate transactions")


@cli.command()
@click.pass_context
def sync(ctx: click.Context):
    """
    Sync all transactions with database
    """
    info("Getting accounts details")
    res = get(ctx, "/requisitions/")
    accounts = []
    for r in res.get("results", []):
        accounts += r.get("accounts", [])
    accounts = list(set(accounts))

    info(f"Syncing transactions for {len(accounts)} accounts")

    for account in accounts:
        try:
            save_transactions(ctx, account)
        except Exception as e:
            error(f"[{account}] Error: Sync failed, skipping account. Exception: {e}")
