"""SQLModel database models for Leggen."""

from datetime import datetime
from typing import Optional

from sqlmodel import JSON, Column, Field, SQLModel


class Account(SQLModel, table=True):
    """Account model."""

    __tablename__ = "accounts"

    id: str = Field(primary_key=True)
    institution_id: str = Field(index=True)
    status: str = Field(index=True)
    iban: Optional[str] = None
    name: Optional[str] = None
    currency: Optional[str] = None
    created: datetime
    last_accessed: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    display_name: Optional[str] = None
    logo: Optional[str] = None


class Balance(SQLModel, table=True):
    """Balance model."""

    __tablename__ = "balances"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: str = Field(index=True)
    bank: str
    status: str
    iban: str
    amount: float
    currency: str
    type: str
    timestamp: datetime = Field(index=True)


class Transaction(SQLModel, table=True):
    """Transaction model."""

    __tablename__ = "transactions"

    accountId: str = Field(primary_key=True)
    transactionId: str = Field(primary_key=True)
    internalTransactionId: Optional[str] = Field(default=None, index=True)
    institutionId: str
    iban: Optional[str] = None
    transactionDate: Optional[datetime] = Field(default=None, index=True)
    description: Optional[str] = None
    transactionValue: Optional[float] = Field(default=None, index=True)
    transactionCurrency: Optional[str] = None
    transactionStatus: Optional[str] = None
    rawTransaction: dict = Field(sa_column=Column(JSON))


class TransactionEnrichment(SQLModel, table=True):
    """Transaction enrichment model."""

    __tablename__ = "transaction_enrichments"

    accountId: str = Field(primary_key=True, foreign_key="transactions.accountId")
    transactionId: str = Field(
        primary_key=True, foreign_key="transactions.transactionId"
    )
    clean_name: Optional[str] = Field(default=None, index=True)
    category: Optional[str] = Field(default=None, index=True)
    logo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SyncOperation(SQLModel, table=True):
    """Sync operation model."""

    __tablename__ = "sync_operations"

    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: datetime = Field(index=True)
    completed_at: Optional[datetime] = None
    success: Optional[bool] = Field(default=None, index=True)
    accounts_processed: int = Field(default=0)
    transactions_added: int = Field(default=0)
    transactions_updated: int = Field(default=0)
    balances_updated: int = Field(default=0)
    duration_seconds: Optional[float] = None
    errors: Optional[str] = None
    logs: Optional[str] = None
    trigger_type: str = Field(default="manual", index=True)
