import click

from leggen.main import cli
from leggen.utils.disk import save_file
from leggen.utils.network import get, post
from leggen.utils.text import info, print_table, warning


@cli.command()
@click.pass_context
def add(ctx):
    """
    Connect to a bank
    """
    country = click.prompt(
        "Bank Country",
        type=click.Choice(
            [
                "AT",
                "BE",
                "BG",
                "HR",
                "CY",
                "CZ",
                "DK",
                "EE",
                "FI",
                "FR",
                "DE",
                "GR",
                "HU",
                "IS",
                "IE",
                "IT",
                "LV",
                "LI",
                "LT",
                "LU",
                "MT",
                "NL",
                "NO",
                "PL",
                "PT",
                "RO",
                "SK",
                "SI",
                "ES",
                "SE",
                "GB",
            ],
            case_sensitive=True,
        ),
        default="PT",
    )
    info(f"Getting bank list for country: {country}")
    banks = get(ctx, "/institutions/", {"country": country})
    filtered_banks = [
        {
            "id": bank["id"],
            "name": bank["name"],
            "max_transaction_days": bank["transaction_total_days"],
        }
        for bank in banks
    ]
    print_table(filtered_banks)
    allowed_ids = [str(bank["id"]) for bank in banks]
    bank_id = click.prompt("Bank ID", type=click.Choice(allowed_ids))
    click.confirm("Do you agree to connect to this bank?", abort=True)

    info(f"Connecting to bank with ID: {bank_id}")

    res = post(
        ctx,
        "/requisitions/",
        {"institution_id": bank_id, "redirect": "http://localhost:8000/"},
    )

    save_file(f"req_{res['id']}.json", res)

    warning(f"Please open the following URL in your browser to accept: {res['link']}")
