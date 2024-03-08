import click

from leggen.main import cli
from leggen.utils.gocardless import REQUISITION_STATUS
from leggen.utils.network import get
from leggen.utils.text import datefmt, echo, info, print_table


@cli.command()
@click.pass_context
def status(ctx: click.Context):
    """
    List all connected banks and their status
    """

    res = get(ctx, "/requisitions/")
    requisitions = []
    accounts = set()
    for r in res["results"]:
        requisitions.append(
            {
                "Bank": r["institution_id"],
                "Status": REQUISITION_STATUS.get(r["status"], "UNKNOWN"),
                "Created at": datefmt(r["created"]),
                "Requisition ID": r["id"],
            }
        )
        accounts.update(r.get("accounts", []))
    info("Banks")
    print_table(requisitions)

    account_details = []
    for account in accounts:
        details = get(ctx, f"/accounts/{account}")
        account_details.append(
            {
                "ID": details["id"],
                "Bank": details["institution_id"],
                "Status": details["status"],
                "IBAN": details.get("iban", "N/A"),
                "Created at": datefmt(details["created"]),
                "Last accessed at": datefmt(details["last_accessed"]),
            }
        )
    echo()
    info("Accounts")
    print_table(account_details)
