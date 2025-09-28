"""API models for backup endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class S3Config(BaseModel):
    """S3 backup configuration model for API."""

    access_key_id: str = Field(..., description="AWS S3 access key ID")
    secret_access_key: str = Field(..., description="AWS S3 secret access key")
    bucket_name: str = Field(..., description="S3 bucket name")
    region: str = Field(default="us-east-1", description="AWS S3 region")
    endpoint_url: Optional[str] = Field(
        default=None, description="Custom S3 endpoint URL"
    )
    path_style: bool = Field(default=False, description="Use path-style addressing")
    enabled: bool = Field(default=True, description="Enable S3 backups")


class BackupSettings(BaseModel):
    """Backup settings model for API."""

    s3: Optional[S3Config] = None


class BackupTest(BaseModel):
    """Backup connection test request model."""

    service: str = Field(..., description="Backup service type (s3)")
    config: S3Config = Field(..., description="S3 configuration to test")


class BackupInfo(BaseModel):
    """Backup file information model."""

    key: str = Field(..., description="S3 object key")
    last_modified: str = Field(..., description="Last modified timestamp (ISO format)")
    size: int = Field(..., description="File size in bytes")


class BackupOperation(BaseModel):
    """Backup operation request model."""

    operation: str = Field(..., description="Operation type (backup, restore)")
    backup_key: Optional[str] = Field(
        default=None, description="Backup key for restore operations"
    )
