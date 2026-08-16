from datetime import datetime

from pydantic import BaseModel


class SyncOperation(BaseModel):
    """Sync operation record for tracking sync history"""

    id: int | None = None
    started_at: datetime
    completed_at: datetime | None = None
    success: bool | None = None
    accounts_processed: int = 0
    transactions_added: int = 0
    transactions_updated: int = 0
    balances_updated: int = 0
    duration_seconds: float | None = None
    errors: list[str] = []
    logs: list[str] = []
    trigger_type: str = "manual"  # manual, scheduled, retry, api


class SyncRequest(BaseModel):
    """Request to trigger a sync"""

    account_ids: list[str] | None = None  # If None, sync all accounts
    full_sync: bool = False  # If False, only sync last 30 days of transactions


class SyncStatus(BaseModel):
    """Sync operation status"""

    is_running: bool
    last_sync: datetime | None = None
    next_sync: datetime | None = None
    accounts_synced: int = 0
    total_accounts: int = 0
    transactions_added: int = 0
    errors: list[str] = []


class SyncScheduleRequest(BaseModel):
    """Request to update sync schedule"""

    enabled: bool = True
    hour: int = 3
    minute: int = 0
    cron: str | None = None


class SyncScheduleResponse(BaseModel):
    """Response with current sync schedule"""

    enabled: bool
    hour: int
    minute: int
    cron: str | None = None
    next_sync_time: str | None = None


class SyncResult(BaseModel):
    """Result of a sync operation"""

    success: bool
    accounts_processed: int
    transactions_added: int
    transactions_updated: int
    balances_updated: int
    duration_seconds: float
    errors: list[str] = []
    started_at: datetime
    completed_at: datetime
