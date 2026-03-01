import click

from leggen.api_client import LeggenAPIClient
from leggen.main import cli
from leggen.utils.text import error, info, success


@cli.command()
@click.option("--full", is_flag=True, help="Full sync instead of last 30 days only")
@click.pass_context
def sync(ctx: click.Context, full: bool):
    """
    Sync all transactions with database
    """
    api_client = LeggenAPIClient(
        ctx.obj.get("api_url"), verify_ssl=ctx.obj.get("verify_ssl", True)
    )

    # Check if leggen server is available
    if not api_client.health_check():
        error("Cannot connect to leggen server. Please ensure it's running.")
        return

    try:
        info("Starting sync...")
        result = api_client.trigger_sync(full_sync=full)

        if result.get("success"):
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
        else:
            error("Sync failed")
            if result.get("errors"):
                for err in result["errors"]:
                    error(f"  - {err}")

    except Exception as e:
        error(f"Sync failed: {str(e)}")
        return
