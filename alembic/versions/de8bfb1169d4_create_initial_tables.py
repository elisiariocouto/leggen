"""create_initial_tables

Revision ID: de8bfb1169d4
Revises:
Create Date: 2025-09-30 23:09:24.255875

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "de8bfb1169d4"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database tables."""
    # Create accounts table
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("institution_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("iban", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("last_accessed", sa.DateTime(), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_accounts_institution_id", "accounts", ["institution_id"])
    op.create_index("idx_accounts_status", "accounts", ["status"])

    # Create balances table
    op.create_table(
        "balances",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("account_id", sa.String(), nullable=False),
        sa.Column("bank", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("iban", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_balances_account_id", "balances", ["account_id"])
    op.create_index("idx_balances_timestamp", "balances", ["timestamp"])
    op.create_index(
        "idx_balances_account_type_timestamp",
        "balances",
        ["account_id", "type", "timestamp"],
    )

    # Create transactions table (old schema with internalTransactionId as PK)
    op.create_table(
        "transactions",
        sa.Column("accountId", sa.String(), nullable=False),
        sa.Column("transactionId", sa.String(), nullable=False),
        sa.Column("internalTransactionId", sa.String(), nullable=True),
        sa.Column("institutionId", sa.String(), nullable=False),
        sa.Column("iban", sa.String(), nullable=True),
        sa.Column("transactionDate", sa.DateTime(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("transactionValue", sa.Float(), nullable=True),
        sa.Column("transactionCurrency", sa.String(), nullable=True),
        sa.Column("transactionStatus", sa.String(), nullable=True),
        sa.Column("rawTransaction", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("internalTransactionId"),
    )
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
    """Drop initial tables."""
    op.drop_table("transactions")
    op.drop_table("balances")
    op.drop_table("accounts")
