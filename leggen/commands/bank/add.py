import click

from leggen.api_client import LeggenAPIClient
from leggen.main import cli
from leggen.utils.disk import save_file
from leggen.utils.text import info, print_table, success, warning


@cli.command()
@click.pass_context
def add(ctx):
    """
    Connect to a bank
    """
    api_client = LeggenAPIClient(ctx.obj.get("api_url"))

    # Check if leggen server is available
    if not api_client.health_check():
        click.echo(
            "Error: Cannot connect to leggen server. Please ensure it's running."
        )
        return

    try:
        # Get supported countries
        countries = api_client.get_supported_countries()
        country_codes = [c["code"] for c in countries]

        country = click.prompt(
            "Bank Country",
            type=click.Choice(country_codes, case_sensitive=True),
            default="PT",
        )

        info(f"Getting bank list for country: {country}")
        banks = api_client.get_institutions(country)

        if not banks:
            warning(f"No banks available for country {country}")
            return

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

        # Show bank details
        selected_bank = next(bank for bank in banks if bank["id"] == bank_id)
        info(f"Selected bank: {selected_bank['name']}")

        click.confirm("Do you agree to connect to this bank?", abort=True)

        info(f"Connecting to bank with ID: {bank_id}")

        # Connect to bank via API
        result = api_client.connect_to_bank(bank_id, "http://localhost:8000/")

        # Save requisition details
        save_file(f"req_{result['id']}.json", result)

        success("Bank connection request created successfully!")
        warning(
            "Please open the following URL in your browser to complete the authorization:"
        )
        click.echo(f"\n{result['link']}\n")

        info(f"Requisition ID: {result['id']}")
        info(
            "After completing the authorization, you can check the connection status with 'leggen status'"
        )

    except Exception as e:
        click.echo(f"Error: Failed to connect to bank: {str(e)}")
