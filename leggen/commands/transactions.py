import click

from leggen.api_client import LeggenAPIClient
from leggen.main import cli
from leggen.utils.text import datefmt, info, print_table


@cli.command()
@click.option("-a", "--account", type=str, help="Account ID")
@click.option(
    "-l", "--limit", type=int, default=50, help="Number of transactions to show"
)
@click.option("--full", is_flag=True, help="Show full transaction details")
@click.pass_context
def transactions(ctx: click.Context, account: str, limit: int, full: bool):
    """
    List transactions

    By default, this command lists all transactions for all accounts.

    If the --account option is used, it will only list transactions for that account.
    """
    api_client = LeggenAPIClient(ctx.obj.get("api_url"))

    # Check if leggen server is available
    if not api_client.health_check():
        click.echo(
            "Error: Cannot connect to leggen server. Please ensure it's running."
        )
        return

    try:
        if account:
            # Get transactions for specific account
            account_details = api_client.get_account_details(account)
            transactions_data = api_client.get_account_transactions(
                account, limit=limit, summary_only=not full
            )

            info(f"Bank: {account_details['institution_id']}")
            info(f"IBAN: {account_details.get('iban', 'N/A')}")

        else:
            # Get all transactions
            transactions_data = api_client.get_all_transactions(
                limit=limit, summary_only=not full, account_id=account
            )

        # Format transactions for display
        if full:
            # Full transaction details
            formatted_transactions = []
            for txn in transactions_data:
                # Handle optional internal_transaction_id
                txn_id = txn.get("internal_transaction_id")
                txn_id_display = txn_id[:12] + "..." if txn_id else "N/A"

                formatted_transactions.append(
                    {
                        "ID": txn_id_display,
                        "Date": datefmt(txn["transaction_date"]),
                        "Description": txn["description"][:50] + "..."
                        if len(txn["description"]) > 50
                        else txn["description"],
                        "Amount": f"{txn['transaction_value']:.2f} {txn['transaction_currency']}",
                        "Status": txn["transaction_status"].upper(),
                        "Account": txn["account_id"][:8] + "...",
                    }
                )
        else:
            # Summary view
            formatted_transactions = []
            for txn in transactions_data:
                # Handle optional internal_transaction_id
                txn_id = txn.get("internal_transaction_id")

                formatted_transactions.append(
                    {
                        "Date": datefmt(txn["date"]),
                        "Description": txn["description"][:60] + "..."
                        if len(txn["description"]) > 60
                        else txn["description"],
                        "Amount": f"{txn['amount']:.2f} {txn['currency']}",
                        "Status": txn["status"].upper(),
                    }
                )

        if formatted_transactions:
            print_table(formatted_transactions)
            info(f"Showing {len(formatted_transactions)} transactions")
        else:
            info("No transactions found")

    except Exception as e:
        click.echo(f"Error: Failed to get transactions: {str(e)}")
