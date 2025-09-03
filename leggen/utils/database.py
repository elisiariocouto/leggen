from datetime import datetime

import click

import leggen.database.sqlite as sqlite_engine
from leggen.utils.text import info, warning


def persist_balance(ctx: click.Context, account: str, balance: dict) -> None:
    sqlite = ctx.obj.get("database", {}).get("sqlite", True)

    if not sqlite:
        warning("SQLite database is disabled, skipping balance saving")
        return

    info(f"[{account}] Fetched balances, saving to SQLite")
    sqlite_engine.persist_balances(ctx, balance)


def persist_transactions(ctx: click.Context, account: str, transactions: list) -> list:
    sqlite = ctx.obj.get("database", {}).get("sqlite", True)

    if not sqlite:
        warning("SQLite database is disabled, skipping transaction saving")
        # WARNING: This will return the transactions list as is, without saving it to any database
        # Possible duplicate notifications will be sent if the filters are enabled
        return transactions

    info(f"[{account}] Fetched {len(transactions)} transactions, saving to SQLite")
    return sqlite_engine.persist_transactions(ctx, account, transactions)


def save_transactions(ctx: click.Context, account: str) -> list:
    import requests

    api_url = ctx.obj.get("api_url", "http://localhost:8000")

    info(f"[{account}] Getting account details")
    res = requests.get(f"{api_url}/accounts/{account}")
    res.raise_for_status()
    account_info = res.json()

    info(f"[{account}] Getting transactions")
    transactions = []

    res = requests.get(f"{api_url}/accounts/{account}/transactions/")
    res.raise_for_status()
    account_transactions = res.json().get("transactions", [])

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
