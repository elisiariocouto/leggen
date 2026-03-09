import click

from leggen.utils.auth import generate_api_key, generate_jwt_secret, hash_password


@click.command()
@click.option(
    "--username",
    default="admin",
    show_default=True,
    help="Username for authentication",
)
@click.pass_context
def generate_auth_config(ctx: click.Context, username: str) -> None:
    """Generate an [auth] configuration block for config.toml."""
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

    password_hash = hash_password(password)
    api_key = generate_api_key()
    jwt_secret = generate_jwt_secret()

    click.echo("\n# Add this to your config.toml:\n")
    click.echo("[auth]")
    click.echo(f'username = "{username}"')
    click.echo(f'password_hash = "{password_hash}"')
    click.echo(f'api_key = "{api_key}"')
    click.echo(f'jwt_secret = "{jwt_secret}"')
    click.echo("jwt_expiry_minutes = 60")
