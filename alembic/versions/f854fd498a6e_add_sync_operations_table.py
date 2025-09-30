"""add_sync_operations_table

Add sync_operations table for tracking synchronization operations.

Revision ID: f854fd498a6e
Revises: be8d5807feca
Create Date: 2025-09-30 23:16:35.229062

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f854fd498a6e"
down_revision: Union[str, Sequence[str], None] = "be8d5807feca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create sync_operations table."""
    op.create_table(
        "sync_operations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column(
            "accounts_processed", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "transactions_added", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "transactions_updated", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("balances_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("errors", sa.String(), nullable=True),
        sa.Column("logs", sa.String(), nullable=True),
        sa.Column("trigger_type", sa.String(), nullable=False, server_default="manual"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_sync_operations_started_at", "sync_operations", ["started_at"])
    op.create_index("idx_sync_operations_success", "sync_operations", ["success"])
    op.create_index(
        "idx_sync_operations_trigger_type", "sync_operations", ["trigger_type"]
    )


def downgrade() -> None:
    """Drop sync_operations table."""
    op.drop_table("sync_operations")
