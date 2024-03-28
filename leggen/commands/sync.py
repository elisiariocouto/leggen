from datetime import datetime

import click

from leggen.main import cli
from leggen.utils.mongo import save_transactions as save_transactions_mongo
from leggen.utils.network import get
from leggen.utils.sqlite import save_transactions as save_transactions_sqlite
from leggen.utils.text import error, info


def save_transactions(ctx: click.Context, account: str):
    info(f"[{account}] Getting account details")
    account_info = get(ctx, f"/accounts/{account}")

    info(f"[{account}] Getting transactions")
    transactions = []

    account_transactions = get(ctx, f"/accounts/{account}/transactions/").get(
        "transactions", []
    )

    for transaction in account_transactions.get("booked", []):
        booked_date = transaction.get("bookingDateTime") or transaction.get(
            "bookingDate"
        )
        value_date = transaction.get("valueDateTime") or transaction.get("valueDate")
        if booked_date and value_date:
            min_date = min(
                datetime.fromisoformat(booked_date), datetime.fromisoformat(value_date)
            )
        else:
            min_date = datetime.fromisoformat(booked_date or value_date)

        transactionValue = float(
            transaction.get("transactionAmount", {}).get("amount", 0)
        )
        currency = transaction.get("transactionAmount", {}).get("currency", "")

        description = transaction.get(
            "remittanceInformationUnstructured",
            ",".join(transaction.get("remittanceInformationUnstructuredArray", [])),
        )

        t = {
            "internalTransactionId": transaction.get("internalTransactionId"),
            "institutionId": account_info["institution_id"],
            "iban": account_info.get("iban", "N/A"),
            "transactionDate": min_date,
            "description": description,
            "transactionValue": transactionValue,
            "transactionCurrency": currency,
            "transactionStatus": "booked",
            "accountId": account,
            "rawTransaction": transaction,
        }
        transactions.append(t)

    for transaction in account_transactions.get("pending", []):
        booked_date = transaction.get("bookingDateTime") or transaction.get(
            "bookingDate"
        )
        value_date = transaction.get("valueDateTime") or transaction.get("valueDate")
        if booked_date and value_date:
            min_date = min(
                datetime.fromisoformat(booked_date), datetime.fromisoformat(value_date)
            )
        else:
            min_date = datetime.fromisoformat(booked_date or value_date)

        transactionValue = float(
            transaction.get("transactionAmount", {}).get("amount", 0)
        )
        currency = transaction.get("transactionAmount", {}).get("currency", "")

        description = transaction.get(
            "remittanceInformationUnstructured",
            ",".join(transaction.get("remittanceInformationUnstructuredArray", [])),
        )

        t = {
            "internalTransactionId": transaction.get("internalTransactionId"),
            "institutionId": account_info["institution_id"],
            "iban": account_info.get("iban", "N/A"),
            "transactionDate": min_date,
            "description": description,
            "transactionValue": transactionValue,
            "transactionCurrency": currency,
            "transactionStatus": "pending",
            "accountId": account,
            "rawTransaction": transaction,
        }
        transactions.append(t)

    sqlite = ctx.obj.get("database", {}).get("sqlite", True)
    info(
        f"[{account}] Fetched {len(transactions)} transactions, saving to {'SQLite' if sqlite else 'MongoDB'}"
    )
    if sqlite:
        save_transactions_sqlite(ctx, account, transactions)
    else:
        save_transactions_mongo(ctx, account, transactions)


@cli.command()
@click.pass_context
def sync(ctx: click.Context):
    """
    Sync all transactions with database
    """
    info("Getting accounts details")
    res = get(ctx, "/requisitions/")
    accounts = set()
    for r in res.get("results", []):
        accounts.update(r.get("accounts", []))

    info(f"Syncing transactions for {len(accounts)} accounts")

    for account in accounts:
        try:
            save_transactions(ctx, account)
        except Exception as e:
            error(f"[{account}] Error: Sync failed, skipping account, exception: {e}")
