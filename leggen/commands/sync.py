import click

from leggen.api_client import LeggenAPIClient
from leggen.main import cli
from leggen.utils.text import error, info, success


@cli.command()
@click.option("--wait", is_flag=True, help="Wait for sync to complete (synchronous)")
@click.option("--force", is_flag=True, help="Force sync even if already running")
@click.pass_context
def sync(ctx: click.Context, wait: bool, force: bool):
    """
    Sync all transactions with database
    """
    api_client = LeggenAPIClient(ctx.obj.get("api_url"))

    # Check if leggen server is available
    if not api_client.health_check():
        error("Cannot connect to leggen server. Please ensure it's running.")
        return

    try:
        if wait:
            # Run sync synchronously and wait for completion
            info("Starting synchronous sync...")
            result = api_client.sync_now(force=force)

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
        else:
            # Trigger async sync
            info("Starting background sync...")
            result = api_client.trigger_sync(force=force)

            if result.get("sync_started"):
                success("Sync started successfully in the background")
                info(
                    "Use 'leggen sync --wait' to run synchronously or check status with API"
                )
            else:
                error("Failed to start sync")

    except Exception as e:
        error(f"Sync failed: {str(e)}")
        return
