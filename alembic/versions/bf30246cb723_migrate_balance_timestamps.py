"""migrate_balance_timestamps

Convert Unix timestamps to datetime strings in balances table.

Revision ID: bf30246cb723
Revises: de8bfb1169d4
Create Date: 2025-09-30 23:14:03.128959

"""

from datetime import datetime
from typing import Sequence, Union

from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bf30246cb723"
down_revision: Union[str, Sequence[str], None] = "de8bfb1169d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert all Unix timestamps to datetime strings."""
    conn = op.get_bind()

    # Get all balances with REAL timestamps
    result = conn.execute(
        text("""
        SELECT id, timestamp
        FROM balances
        WHERE typeof(timestamp) = 'real'
        ORDER BY id
    """)
    )

    unix_records = result.fetchall()

    if not unix_records:
        return

    # Convert and update in batches
    for record_id, unix_timestamp in unix_records:
        try:
            # Convert Unix timestamp to datetime string
            dt_string = datetime.fromtimestamp(float(unix_timestamp)).isoformat()

            # Update the record
            conn.execute(
                text("UPDATE balances SET timestamp = :dt WHERE id = :id"),
                {"dt": dt_string, "id": record_id},
            )
        except Exception:
            continue

    conn.commit()


def downgrade() -> None:
    """Not implemented - converting back would lose precision."""
