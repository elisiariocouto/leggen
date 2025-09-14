import click

from leggen.api_client import LeggenAPIClient
from leggen.main import cli
from leggen.utils.text import datefmt, echo, info, print_table


@cli.command()
@click.pass_context
def status(ctx: click.Context):
    """
    List all connected banks and their status
    """
    api_client = LeggenAPIClient(ctx.obj.get("api_url"))

    # Check if leggen server is available
    if not api_client.health_check():
        click.echo(
            "Error: Cannot connect to leggen server. Please ensure it's running."
        )
        return

    # Get bank connection status
    bank_connections = api_client.get_bank_status()
    requisitions = []
    for conn in bank_connections:
        requisitions.append(
            {
                "Bank": conn["bank_id"],
                "Status": conn["status_display"],
                "Created at": datefmt(conn["created_at"]),
                "Requisition ID": conn["requisition_id"],
            }
        )
    info("Banks")
    print_table(requisitions)

    # Get account details
    accounts = api_client.get_accounts()
    account_details = []
    for account in accounts:
        account_details.append(
            {
                "ID": account["id"],
                "Bank": account["institution_id"],
                "Status": account["status"],
                "IBAN": account.get("iban", "N/A"),
                "Created at": datefmt(account["created"]),
                "Last accessed at": (
                    datefmt(account["last_accessed"])
                    if account.get("last_accessed")
                    else "N/A"
                ),
            }
        )
    echo()
    info("Accounts")
    print_table(account_details)
