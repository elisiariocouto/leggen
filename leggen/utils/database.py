from datetime import datetime

import click

import leggen.database.mongo as mongodb_engine
import leggen.database.sqlite as sqlite_engine
from leggen.utils.network import get
from leggen.utils.text import info, warning


def persist_balance(ctx: click.Context, account: str, balance: dict) -> None:
    sqlite = ctx.obj.get("database", {}).get("sqlite", False)
    mongodb = ctx.obj.get("database", {}).get("mongodb", False)

    if not sqlite and not mongodb:
        warning("No database engine is enabled, skipping balance saving")

    if sqlite:
        info(f"[{account}] Fetched balances, saving to SQLite")
        sqlite_engine.persist_balances(ctx, balance)
    else:
        info(f"[{account}] Fetched balances, saving to MongoDB")
        mongodb_engine.persist_balances(ctx, balance)


def persist_transactions(ctx: click.Context, account: str, transactions: list) -> list:
    sqlite = ctx.obj.get("database", {}).get("sqlite", False)
    mongodb = ctx.obj.get("database", {}).get("mongodb", False)

    if not sqlite and not mongodb:
        warning("No database engine is enabled, skipping transaction saving")
        # WARNING: This will return the transactions list as is, without saving it to any database
        # Possible duplicate notifications will be sent if the filters are enabled
        return transactions

    if sqlite:
        info(f"[{account}] Fetched {len(transactions)} transactions, saving to SQLite")
        return sqlite_engine.persist_transactions(ctx, account, transactions)
    else:
        info(f"[{account}] Fetched {len(transactions)} transactions, saving to MongoDB")
        return mongodb_engine.persist_transactions(ctx, account, transactions)


def save_transactions(ctx: click.Context, account: str) -> list:
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

    return persist_transactions(ctx, account, transactions)
