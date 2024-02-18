import click

from leggen.main import cli
from leggen.utils.network import get
from leggen.utils.text import print_table


@cli.command()
@click.argument("account", type=str)
@click.pass_context
def transactions(ctx: click.Context, account: str):
    """
    List transactions for an account

    ACCOUNT is the account id, see 'leggen status' for the account ids
    """
    all_transactions = []
    account_transactions = get(ctx, f"/accounts/{account}/transactions/").get(
        "transactions", []
    )

    for transaction in account_transactions.get("booked", []):
        transaction["TYPE"] = "booked"
        all_transactions.append(transaction)

    for transaction in account_transactions.get("pending", []):
        transaction["TYPE"] = "pending"
        all_transactions.append(transaction)

    print_table(all_transactions)
