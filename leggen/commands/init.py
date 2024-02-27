import click

from leggen.main import cli
from leggen.utils.auth import get_token
from leggen.utils.config import save_config


@cli.command()
@click.option(
    "--api-key",
    prompt=True,
    help="GoCardless API Key",
    envvar="LEGGEN_GC_API_KEY",
    show_envvar=True,
)
@click.option(
    "--api-secret",
    prompt=True,
    help="GoCardless API Secret",
    hide_input=True,
    envvar="LEGGEN_GC_API_SECRET",
    show_envvar=True,
)
@click.option(
    "--api-url",
    default="https://bankaccountdata.gocardless.com/api/v2",
    help="GoCardless API URL",
    show_default=True,
    envvar="LEGGEN_GC_API_URL",
    show_envvar=True,
)
@click.option(
    "--sqlite/--mongo",
    prompt=True,
    default=True,
    help="Use SQLite or MongoDB",
    show_default=True,
)
@click.option(
    "--mongo-uri",
    prompt=True,
    help="MongoDB URI",
    envvar="LEGGEN_MONGO_URI",
    show_envvar=True,
    default="mongodb://localhost:27017",
)
@click.pass_context
def init(
    ctx: click.Context,
    api_key: str,
    api_secret: str,
    api_url: str,
    sqlite: bool,
    mongo_uri: str,
):
    """
    Create configuration file
    """
    config = {
        "api_key": api_key,
        "api_secret": api_secret,
        "api_url": api_url,
        "sqlite": sqlite,
        "mongo_uri": mongo_uri,
    }

    # Just make sure this API credentials are valid
    # if so, it will save the token in the auth file
    _ = get_token(config)

    # Save the configuration
    save_config(config)
