import click

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
    import requests

    info(f"Deleting Bank Requisition: {requisition_id}")

    api_url = ctx.obj.get("api_url", "http://localhost:8000")
    res = requests.delete(f"{api_url}/requisitions/{requisition_id}")
    res.raise_for_status()

    success(f"Bank Requisition {requisition_id} deleted")
