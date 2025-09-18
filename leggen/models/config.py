from typing import List, Optional

from pydantic import BaseModel, Field


class GoCardlessConfig(BaseModel):
    key: str = Field(..., description="GoCardless API key")
    secret: str = Field(..., description="GoCardless API secret")
    url: str = Field(
        default="https://bankaccountdata.gocardless.com/api/v2",
        description="GoCardless API URL",
    )


class DatabaseConfig(BaseModel):
    sqlite: bool = Field(default=True, description="Enable SQLite database")


class DiscordNotificationConfig(BaseModel):
    webhook: str = Field(..., description="Discord webhook URL")
    enabled: bool = Field(default=True, description="Enable Discord notifications")


class TelegramNotificationConfig(BaseModel):
    token: str = Field(..., description="Telegram bot token")
    chat_id: int = Field(..., description="Telegram chat ID")
    enabled: bool = Field(default=True, description="Enable Telegram notifications")


class NotificationConfig(BaseModel):
    discord: Optional[DiscordNotificationConfig] = None
    telegram: Optional[TelegramNotificationConfig] = None


class FilterConfig(BaseModel):
    case_insensitive: Optional[List[str]] = Field(default_factory=list)
    case_sensitive: Optional[List[str]] = Field(default_factory=list)


class SyncScheduleConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enable sync scheduling")
    hour: int = Field(default=3, ge=0, le=23, description="Hour to run sync (0-23)")
    minute: int = Field(default=0, ge=0, le=59, description="Minute to run sync (0-59)")
    cron: Optional[str] = Field(
        default=None, description="Custom cron expression (overrides hour/minute)"
    )


class SchedulerConfig(BaseModel):
    sync: SyncScheduleConfig = Field(default_factory=SyncScheduleConfig)


class Config(BaseModel):
    gocardless: GoCardlessConfig
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    notifications: Optional[NotificationConfig] = None
    filters: Optional[FilterConfig] = None
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
