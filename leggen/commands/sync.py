import click

from leggen.main import cli
from leggen.utils.database import save_transactions
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
