import click

from leggen.main import cli
from leggen.utils.network import get
from leggen.utils.text import datefmt, print_table


@cli.command()
@click.pass_context
def balances(ctx: click.Context):
    """
    List balances of all connected accounts
    """

    res = get(ctx, "/requisitions/")
    accounts = set()
    for r in res.get("results", []):
        accounts.update(r.get("accounts", []))

    all_balances = []
    for account in accounts:
        account_ballances = get(ctx, f"/accounts/{account}/balances/").get(
            "balances", []
        )
        for balance in account_ballances:
            balance_amount = balance["balanceAmount"]
            amount = round(float(balance_amount["amount"]), 2)
            symbol = (
                "€"
                if balance_amount["currency"] == "EUR"
                else f" {balance_amount['currency']}"
            )
            amount_str = f"{amount}{symbol}"
            date = (
                datefmt(balance.get("lastChangeDateTime"))
                if balance.get("lastChangeDateTime")
                else ""
            )
            all_balances.append(
                {
                    "Account": account,
                    "Amount": amount_str,
                    "Type": balance["balanceType"],
                    "Last change at": date,
                }
            )
    print_table(all_balances)
