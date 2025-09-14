import click

from leggen.api_client import LeggenAPIClient
from leggen.main import cli
from leggen.utils.text import datefmt, print_table


@cli.command()
@click.pass_context
def balances(ctx: click.Context):
    """
    List balances of all connected accounts
    """
    api_client = LeggenAPIClient(ctx.obj.get("api_url"))

    # Check if leggen server is available
    if not api_client.health_check():
        click.echo(
            "Error: Cannot connect to leggen server. Please ensure it's running."
        )
        return

    accounts = api_client.get_accounts()

    all_balances = []
    for account in accounts:
        for balance in account.get("balances", []):
            amount = round(float(balance["amount"]), 2)
            symbol = "€" if balance["currency"] == "EUR" else f" {balance['currency']}"
            amount_str = f"{amount}{symbol}"
            date = (
                datefmt(balance.get("last_change_date"))
                if balance.get("last_change_date")
                else ""
            )
            all_balances.append(
                {
                    "Account": account["id"],
                    "Amount": amount_str,
                    "Type": balance["balance_type"],
                    "Last change at": date,
                }
            )
    print_table(all_balances)
