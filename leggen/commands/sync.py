import click

from leggen.api_client import LeggenAPIClient
from leggen.main import cli
from leggen.utils.text import error, info, success


@cli.command()
@click.option("--full", is_flag=True, help="Full sync instead of last 30 days only")
@click.option(
    "-a",
    "--account",
    "accounts",
    multiple=True,
    help="Sync only this account ID (repeatable); defaults to all accounts",
)
@click.pass_context
def sync(ctx: click.Context, full: bool, accounts: tuple[str, ...]):
    """
    Sync transactions with database
    """
    api_client = LeggenAPIClient.from_context(ctx)

    info("Starting sync...")
    result = api_client.trigger_sync(account_ids=list(accounts) or None, full_sync=full)

    if not result.get("success"):
        for err in result.get("errors", []):
            error(f"  - {err}")
        raise click.ClickException("Sync failed")

    success("Sync completed successfully!")
    info(f"Accounts processed: {result.get('accounts_processed', 0)}")
    info(f"Transactions added: {result.get('transactions_added', 0)}")
    info(f"Balances updated: {result.get('balances_updated', 0)}")
    if result.get("duration_seconds"):
        info(f"Duration: {result['duration_seconds']:.2f} seconds")

    if result.get("errors"):
        error(f"Errors encountered: {len(result['errors'])}")
        for err in result["errors"]:
            error(f"  - {err}")
