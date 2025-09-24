import click

from leggen.api_client import LeggenAPIClient
from leggen.main import cli
from leggen.utils.text import info, success


@cli.command()
@click.argument("requisition_id", type=str, required=True, metavar="REQUISITION_ID")
@click.pass_context
def delete(ctx, requisition_id: str):
    """
    Delete bank connection

    REQUISITION_ID: The ID of the Bank Requisition to delete

    Check `leggen status` to get the REQUISITION_ID
    """
    api_client = LeggenAPIClient(ctx.obj.get("api_url"))

    info(f"Deleting Bank Requisition: {requisition_id}")

    # Use API client to make the delete request
    api_client._make_request("DELETE", f"/requisitions/{requisition_id}")

    success(f"Bank Requisition {requisition_id} deleted")
