"""add_display_name_column

Add display_name column to accounts table.

Revision ID: be8d5807feca
Revises: 1ba02efe481c
Create Date: 2025-09-30 23:16:34.929968

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "be8d5807feca"
down_revision: Union[str, Sequence[str], None] = "1ba02efe481c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add display_name column to accounts table."""
    with op.batch_alter_table("accounts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("display_name", sa.String(), nullable=True))


def downgrade() -> None:
    """Remove display_name column."""
    with op.batch_alter_table("accounts", schema=None) as batch_op:
        batch_op.drop_column("display_name")
