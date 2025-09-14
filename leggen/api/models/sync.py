from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SyncRequest(BaseModel):
    """Request to trigger a sync"""

    account_ids: Optional[list[str]] = None  # If None, sync all accounts
    force: bool = False  # Force sync even if recently synced


class SyncStatus(BaseModel):
    """Sync operation status"""

    is_running: bool
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    accounts_synced: int = 0
    total_accounts: int = 0
    transactions_added: int = 0
    errors: list[str] = []

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


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

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SchedulerConfig(BaseModel):
    """Scheduler configuration model"""

    enabled: bool = True
    hour: Optional[int] = 3
    minute: Optional[int] = 0
    cron: Optional[str] = None  # Custom cron expression

    class Config:
        extra = "forbid"
