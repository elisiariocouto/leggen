"""migrate_to_composite_key

Migrate transactions table to use composite primary key (accountId, transactionId).

Revision ID: 1ba02efe481c
Revises: bf30246cb723
Create Date: 2025-09-30 23:16:34.637762

"""

from typing import Sequence, Union

from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1ba02efe481c"
down_revision: Union[str, Sequence[str], None] = "bf30246cb723"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate to composite primary key."""
    conn = op.get_bind()

    # Check if migration is needed
    result = conn.execute(
        text("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='transactions'
    """)
    )

    if not result.fetchone():
        return

    # Create temporary table with new schema
    op.execute("""
        CREATE TABLE transactions_temp (
            accountId TEXT NOT NULL,
            transactionId TEXT NOT NULL,
            internalTransactionId TEXT,
            institutionId TEXT NOT NULL,
            iban TEXT,
            transactionDate DATETIME,
            description TEXT,
            transactionValue REAL,
            transactionCurrency TEXT,
            transactionStatus TEXT,
            rawTransaction JSON NOT NULL,
            PRIMARY KEY (accountId, transactionId)
        )
    """)

    # Insert deduplicated data (keep most recent duplicate)
    op.execute("""
        INSERT INTO transactions_temp
        SELECT
            accountId,
            json_extract(rawTransaction, '$.transactionId') as transactionId,
            internalTransactionId,
            institutionId,
            iban,
            transactionDate,
            description,
            transactionValue,
            transactionCurrency,
            transactionStatus,
            rawTransaction
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY accountId, json_extract(rawTransaction, '$.transactionId')
                       ORDER BY transactionDate DESC, rowid DESC
                   ) as rn
            FROM transactions
            WHERE json_extract(rawTransaction, '$.transactionId') IS NOT NULL
            AND accountId IS NOT NULL
        ) WHERE rn = 1
    """)

    # Replace tables
    op.execute("DROP TABLE transactions")
    op.execute("ALTER TABLE transactions_temp RENAME TO transactions")

    # Recreate indexes
    op.create_index(
        "idx_transactions_internal_id", "transactions", ["internalTransactionId"]
    )
    op.create_index("idx_transactions_date", "transactions", ["transactionDate"])
    op.create_index(
        "idx_transactions_account_date",
        "transactions",
        ["accountId", "transactionDate"],
    )
    op.create_index("idx_transactions_amount", "transactions", ["transactionValue"])


def downgrade() -> None:
    """Not implemented - would require changing primary key back."""
