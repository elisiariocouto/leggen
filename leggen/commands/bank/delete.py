import click

from leggen.main import cli
from leggen.utils.network import delete as http_delete
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
    info(f"Deleting Bank Requisition: {requisition_id}")

    _ = http_delete(
        ctx,
        f"/requisitions/{requisition_id}",
    )

    success(f"Bank Requisition {requisition_id} deleted")
