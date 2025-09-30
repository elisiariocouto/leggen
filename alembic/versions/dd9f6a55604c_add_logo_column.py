"""add_logo_column

Add logo column to accounts table.

Revision ID: dd9f6a55604c
Revises: f854fd498a6e
Create Date: 2025-09-30 23:16:35.530858

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dd9f6a55604c"
down_revision: Union[str, Sequence[str], None] = "f854fd498a6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add logo column to accounts table."""
    with op.batch_alter_table("accounts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("logo", sa.String(), nullable=True))


def downgrade() -> None:
    """Remove logo column."""
    with op.batch_alter_table("accounts", schema=None) as batch_op:
        batch_op.drop_column("logo")
