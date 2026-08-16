from pathlib import Path

from pydantic import BaseModel, Field, FilePath, field_serializer, field_validator


class EnableBankingConfig(BaseModel):
    application_id: str = Field(..., description="EnableBanking application ID")
    key_path: FilePath = Field(..., description="Path to RSA private key PEM file")
    url: str = Field(
        default="https://api.enablebanking.com",
        description="EnableBanking API URL",
    )
    connect_timeout: float = Field(
        default=10.0,
        gt=0,
        description="Seconds to wait for a connection to the EnableBanking API",
    )
    read_timeout: float = Field(
        default=60.0,
        gt=0,
        description=(
            "Seconds to wait for each response chunk. Applies per request, so a"
            " paginated transactions fetch allows this much time for every page."
        ),
    )

    @field_validator("key_path", mode="before")
    @classmethod
    def expand_key_path(cls, v: str | Path) -> Path:
        return Path(v).expanduser()

    @field_serializer("key_path")
    def serialize_key_path(self, value: Path) -> str:
        return str(value)


class DiscordNotificationConfig(BaseModel):
    webhook: str = Field(..., description="Discord webhook URL")
    enabled: bool = Field(default=True, description="Enable Discord notifications")


class TelegramNotificationConfig(BaseModel):
    token: str = Field(..., description="Telegram bot token")
    chat_id: int = Field(..., description="Telegram chat ID")
    enabled: bool = Field(default=True, description="Enable Telegram notifications")


class NotificationConfig(BaseModel):
    discord: DiscordNotificationConfig | None = None
    telegram: TelegramNotificationConfig | None = None


class S3BackupConfig(BaseModel):
    access_key_id: str = Field(..., description="AWS S3 access key ID")
    secret_access_key: str = Field(..., description="AWS S3 secret access key")
    bucket_name: str = Field(..., description="S3 bucket name")
    region: str = Field(default="us-east-1", description="AWS S3 region")
    endpoint_url: str | None = Field(default=None, description="Custom S3 endpoint URL")
    path_style: bool = Field(default=False, description="Use path-style addressing")
    enabled: bool = Field(default=True, description="Enable S3 backups")


class BackupConfig(BaseModel):
    s3: S3BackupConfig | None = None


class FilterConfig(BaseModel):
    case_insensitive: list[str] | None = Field(default_factory=list)
    case_sensitive: list[str] | None = Field(default_factory=list)


class SyncScheduleConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enable sync scheduling")
    hour: int = Field(default=3, ge=0, le=23, description="Hour to run sync (0-23)")
    minute: int = Field(default=0, ge=0, le=59, description="Minute to run sync (0-59)")
    cron: str | None = Field(
        default=None, description="Custom cron expression (overrides hour/minute)"
    )


class BackupScheduleConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enable scheduled S3 backups")
    hour: int = Field(default=4, ge=0, le=23, description="Hour to run backup (0-23)")
    minute: int = Field(
        default=0, ge=0, le=59, description="Minute to run backup (0-59)"
    )
    cron: str | None = Field(
        default=None, description="Custom cron expression (overrides hour/minute)"
    )


class SchedulerConfig(BaseModel):
    sync: SyncScheduleConfig = Field(default_factory=SyncScheduleConfig)
    backup: BackupScheduleConfig = Field(default_factory=BackupScheduleConfig)


class AuthConfig(BaseModel):
    username: str = Field(..., description="Username for authentication")
    password_hash: str = Field(..., description="Bcrypt hashed password")
    api_key: str = Field(..., description="API key for programmatic access")
    jwt_secret: str = Field(..., description="Secret key for JWT token signing")
    jwt_expiry_minutes: int = Field(
        default=60, description="JWT token expiry time in minutes"
    )


class Config(BaseModel):
    auth: AuthConfig | None = None
    enablebanking: EnableBankingConfig
    notifications: NotificationConfig | None = None
    filters: FilterConfig | None = None
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    backup: BackupConfig | None = None
