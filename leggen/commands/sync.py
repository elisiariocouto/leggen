import datetime

import click

from leggen.main import cli
from leggen.utils.database import persist_balance, save_transactions
from leggen.utils.gocardless import REQUISITION_STATUS
from leggen.utils.network import get
from leggen.utils.notifications import send_expire_notification, send_notification
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

    for r in res.get("results", []):
        account_status = REQUISITION_STATUS.get(r["status"], "UNKNOWN")
        if account_status != "LINKED":
            created_at = datetime.datetime.fromisoformat(r["created"])
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            days_left = 90 - (now - created_at).days
            if days_left <= 15:
                n = {
                    "bank": r["institution_id"],
                    "status": REQUISITION_STATUS.get(r["status"], "UNKNOWN"),
                    "created_at": created_at.timestamp(),
                    "requisition_id": r["id"],
                    "days_left": days_left,
                }
                send_expire_notification(ctx, n)

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
                "timestamp": datetime.datetime.now().timestamp(),
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
