import click

from leggen.main import cli
from leggen.utils.network import get
from leggen.utils.text import info, print_table


def print_transactions(
    ctx: click.Context, account_info: dict, account_transactions: dict
):
    info(f"Bank: {account_info['institution_id']}")
    info(f"IBAN: {account_info.get('iban', 'N/A')}")
    all_transactions = []
    for transaction in account_transactions.get("booked", []):
        transaction["TYPE"] = "booked"
        all_transactions.append(transaction)

    for transaction in account_transactions.get("pending", []):
        transaction["TYPE"] = "pending"
        all_transactions.append(transaction)

    print_table(all_transactions)


@cli.command()
@click.option("-a", "--account", type=str, help="Account ID")
@click.pass_context
def transactions(ctx: click.Context, account: str):
    """
    List transactions

    By default, this command lists all transactions for all accounts.

    If the --account option is used, it will only list transactions for that account.
    """
    if account:
        account_info = get(ctx, f"/accounts/{account}")
        account_transactions = get(ctx, f"/accounts/{account}/transactions/").get(
            "transactions", []
        )
        print_transactions(ctx, account_info, account_transactions)
    else:
        res = get(ctx, "/requisitions/")
        accounts = set()
        for r in res["results"]:
            accounts.update(r.get("accounts", []))
        for account in accounts:
            account_details = get(ctx, f"/accounts/{account}")
            account_transactions = get(ctx, f"/accounts/{account}/transactions/").get(
                "transactions", []
            )
            print_transactions(ctx, account_details, account_transactions)
