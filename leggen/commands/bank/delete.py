import click

from leggen.api_client import LeggenAPIClient
from leggen.main import cli
from leggen.utils.text import info, success


@cli.command()
@click.argument("session_id", type=str, required=True, metavar="SESSION_ID")
@click.pass_context
def delete(ctx, session_id: str):
    """
    Delete bank connection

    SESSION_ID: The ID of the bank session to delete

    Check `leggen status` to get the SESSION_ID
    """
    api_client = LeggenAPIClient(ctx.obj.get("api_url"))

    info(f"Deleting bank session: {session_id}")

    api_client.delete_bank_connection(session_id)

    success(f"Bank session {session_id} deleted")
