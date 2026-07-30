import click

from leggen.api_client import LeggenAPIClient
from leggen.utils.text import error, info, success


@click.command()
@click.argument("session_id", type=str, required=True, metavar="SESSION_ID")
@click.pass_context
def delete(ctx, session_id: str):
    """
    Delete bank connection

    SESSION_ID: The ID of the bank session to delete

    Check `leggen status` to get the SESSION_ID
    """
    api_client = LeggenAPIClient(
        ctx.obj.get("api_url"),
        verify_ssl=ctx.obj.get("verify_ssl", True),
        api_key=ctx.obj.get("api_key"),
    )

    # Check if leggen server is available
    if not api_client.health_check():
        error("Cannot connect to leggen server. Please ensure it's running.")
        ctx.exit(1)

    info(f"Deleting bank session: {session_id}")

    try:
        api_client.delete_bank_connection(session_id)
    except Exception as e:
        error(f"Failed to delete bank session {session_id}: {str(e)}")
        ctx.exit(1)

    success(f"Bank session {session_id} deleted")
