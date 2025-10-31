"""add_transaction_enrichments_table

Add transaction_enrichments table for storing enriched transaction data.

Revision ID: 4819c868ebc1
Revises: dd9f6a55604c
Create Date: 2025-09-30 23:20:00.969614

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4819c868ebc1"
down_revision: Union[str, Sequence[str], None] = "dd9f6a55604c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create transaction_enrichments table."""
    op.create_table(
        "transaction_enrichments",
        sa.Column("accountId", sa.String(), nullable=False),
        sa.Column("transactionId", sa.String(), nullable=False),
        sa.Column("clean_name", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["accountId", "transactionId"],
            ["transactions.accountId", "transactions.transactionId"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("accountId", "transactionId"),
    )

    # Create indexes
    op.create_index(
        "idx_transaction_enrichments_category", "transaction_enrichments", ["category"]
    )
    op.create_index(
        "idx_transaction_enrichments_clean_name",
        "transaction_enrichments",
        ["clean_name"],
    )


def downgrade() -> None:
    """Drop transaction_enrichments table."""
    op.drop_table("transaction_enrichments")
