from urllib.parse import parse_qs, urlparse

import click

from leggen.api_client import LeggenAPIClient
from leggen.main import cli
from leggen.utils.text import info, print_table, success, warning


@cli.command()
@click.pass_context
def add(ctx):
    """
    Connect to a bank
    """
    api_client = LeggenAPIClient(
        ctx.obj.get("api_url"),
        verify_ssl=ctx.obj.get("verify_ssl", True),
        api_key=ctx.obj.get("api_key"),
    )

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
                "name": bank["name"],
                "country": bank.get("country", country),
                "bic": bank.get("bic", ""),
            }
            for bank in banks
        ]
        print_table(filtered_banks)

        allowed_names = [str(bank["name"]) for bank in banks]
        bank_name = click.prompt("Bank Name", type=click.Choice(allowed_names))

        # Show bank details
        info(f"Selected bank: {bank_name}")

        click.confirm("Do you agree to connect to this bank?", abort=True)

        info(f"Connecting to bank: {bank_name}")

        # Connect to bank via API
        result = api_client.connect_to_bank(bank_name, country)

        success("Bank authorization request created!")
        warning(
            "Please open the following URL in your browser to authorize the connection:"
        )
        click.echo(f"\n{result['url']}\n")

        info("After completing the authorization, paste the callback URL here.")
        callback_url = click.prompt("Callback URL")

        # Parse the code from the callback URL
        parsed = urlparse(callback_url)
        query_params = parse_qs(parsed.query)
        code = query_params.get("code", [None])[0]

        if not code:
            click.echo("Error: No authorization code found in the callback URL.")
            return

        # Exchange the code for a session
        session = api_client.exchange_auth_code(code)

        success("Bank connection established!")
        info(f"Session ID: {session['session_id']}")
        info(f"Bank: {session['aspsp_name']} ({session['aspsp_country']})")
        accounts = session.get("accounts", [])
        info(f"Accounts: {len(accounts) if accounts else 0}")
        info("You can now sync your accounts with 'leggen sync'")

    except Exception as e:
        click.echo(f"Error: Failed to connect to bank: {str(e)}")
