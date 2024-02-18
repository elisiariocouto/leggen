import click

from leggen.main import cli
from leggen.utils.auth import get_token
from leggen.utils.config import save_config


@cli.command()
@click.option(
    "--api-key", prompt=True, help="GoCardless API Key", envvar="LEGGEN_GC_API_KEY"
)
@click.option(
    "--api-secret",
    prompt=True,
    help="GoCardless API Secret",
    hide_input=True,
    envvar="LEGGEN_GC_API_SECRET",
)
@click.option(
    "--api-url",
    default="https://bankaccountdata.gocardless.com/api/v2",
    help="GoCardless API URL",
    show_default=True,
    envvar="LEGGEN_GC_API_URL",
)
@click.option("--mongo-uri", prompt=True, help="MongoDB URI", envvar="LEGGEN_MONGO_URI")
@click.pass_context
def init(ctx: click.Context, api_key, api_secret, api_url, mongo_uri):
    """
    Create configuration file
    """
    config = {
        "api_key": api_key,
        "api_secret": api_secret,
        "api_url": api_url,
        "mongo_uri": mongo_uri,
    }

    # Just make sure this API credentials are valid
    # if so, it will save the token in the auth file
    _ = get_token(config)

    # Save the configuration
    save_config(config)
