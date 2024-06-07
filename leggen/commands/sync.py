from datetime import datetime

import click

from leggen.main import cli
from leggen.utils.database import persist_balance, save_transactions
from leggen.utils.network import get
from leggen.utils.notifications import send_notification
from leggen.utils.text import error, info


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

    info(f"Syncing balances for {len(accounts)} accounts")

    for account in accounts:
        account_details = get(ctx, f"/accounts/{account}")
        account_balances = get(ctx, f"/accounts/{account}/balances/").get(
            "balances", []
        )
        for balance in account_balances:
            balance_amount = balance["balanceAmount"]
            amount = round(float(balance_amount["amount"]), 2)
            balance_document = {
                "account_id": account,
                "bank": account_details["institution_id"],
                "status": account_details["status"],
                "iban": account_details.get("iban", "N/A"),
                "amount": amount,
                "currency": balance_amount["currency"],
                "type": balance["balanceType"],
                "timestamp": datetime.now().timestamp(),
            }
            try:
                persist_balance(ctx, account, balance_document)
            except Exception as e:
                error(
                    f"[{account}] Error: Sync failed, skipping account, exception: {e}"
                )
                continue

    info(f"Syncing transactions for {len(accounts)} accounts")

    for account in accounts:
        try:
            new_transactions = save_transactions(ctx, account)
        except Exception as e:
            error(f"[{account}] Error: Sync failed, skipping account, exception: {e}")
            continue
        try:
            send_notification(ctx, new_transactions)
        except Exception as e:
            error(f"[{account}] Error: Notification failed, exception: {e}")
            continue
