"""API models for backup endpoints."""

from typing import Literal

from pydantic import BaseModel, Field

from leggen.models.config import S3BackupConfig


class S3Config(S3BackupConfig):
    """The S3 section as the API exchanges it.

    Same fields as the config model; on reads the two secrets are masked, and
    on writes a masked value means "keep what is stored".
    """


class BackupSettings(BaseModel):
    """Backup settings model for API."""

    s3: S3Config | None = None


class BackupTest(BaseModel):
    """Backup connection test request model."""

    service: Literal["s3"] = Field(description="Backup service type")
    config: S3Config = Field(..., description="S3 configuration to test")


class BackupInfo(BaseModel):
    """Metadata of one stored backup"""

    key: str
    last_modified: str
    size: int


class BackupOperation(BaseModel):
    """Backup operation request model."""

    operation: Literal["backup", "restore"]
    backup_key: str | None = Field(
        default=None, description="Backup key for restore operations"
    )
