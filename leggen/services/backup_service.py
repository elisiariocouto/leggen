"""Backup service for S3 storage."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from loguru import logger

from leggen.models.config import S3BackupConfig


class BackupService:
    """Service for managing S3 backups."""

    def __init__(self, s3_config: Optional[S3BackupConfig] = None):
        """Initialize backup service with S3 configuration."""
        self.s3_config = s3_config
        self._s3_client = None

    def _get_s3_client(self, config: Optional[S3BackupConfig] = None):
        """Get or create S3 client with current configuration."""
        current_config = config or self.s3_config
        if not current_config:
            raise ValueError("S3 configuration is required")

        # Create S3 client with configuration
        session = boto3.Session(
            aws_access_key_id=current_config.access_key_id,
            aws_secret_access_key=current_config.secret_access_key,
            region_name=current_config.region,
        )

        s3_kwargs = {}
        if current_config.endpoint_url:
            s3_kwargs["endpoint_url"] = current_config.endpoint_url

        if current_config.path_style:
            from botocore.config import Config

            s3_kwargs["config"] = Config(s3={"addressing_style": "path"})

        return session.client("s3", **s3_kwargs)

    async def test_connection(self, config: S3BackupConfig) -> bool:
        """Test S3 connection with provided configuration.

        Args:
            config: S3 configuration to test

        Returns:
            True if connection successful, False otherwise
        """
        try:
            s3_client = self._get_s3_client(config)

            # Try to list objects in the bucket (limited to 1 to minimize cost)
            s3_client.list_objects_v2(Bucket=config.bucket_name, MaxKeys=1)

            logger.info(
                f"S3 connection test successful for bucket: {config.bucket_name}"
            )
            return True

        except NoCredentialsError:
            logger.error("S3 credentials not found or invalid")
            return False
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(
                f"S3 connection test failed: {error_code} - {e.response['Error']['Message']}"
            )
            return False
        except Exception as e:
            logger.error(f"Unexpected error during S3 connection test: {str(e)}")
            return False

    async def backup_database(self, database_path: Path) -> bool:
        """Backup database file to S3.

        Args:
            database_path: Path to the SQLite database file

        Returns:
            True if backup successful, False otherwise
        """
        if not self.s3_config or not self.s3_config.enabled:
            logger.warning("S3 backup is not configured or disabled")
            return False

        if not database_path.exists():
            logger.error(f"Database file not found: {database_path}")
            return False

        try:
            s3_client = self._get_s3_client()

            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_key = f"leggen_backups/database_backup_{timestamp}.db"

            # Upload database file
            logger.info(f"Starting database backup to S3: {backup_key}")
            s3_client.upload_file(
                str(database_path), self.s3_config.bucket_name, backup_key
            )

            logger.info(f"Database backup completed successfully: {backup_key}")
            return True

        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            return False

    async def list_backups(self) -> list[dict]:
        """List available backups in S3.

        Returns:
            List of backup metadata dictionaries
        """
        if not self.s3_config or not self.s3_config.enabled:
            logger.warning("S3 backup is not configured or disabled")
            return []

        try:
            s3_client = self._get_s3_client()

            # List objects with backup prefix
            response = s3_client.list_objects_v2(
                Bucket=self.s3_config.bucket_name, Prefix="leggen_backups/"
            )

            backups = []
            for obj in response.get("Contents", []):
                backups.append(
                    {
                        "key": obj["Key"],
                        "last_modified": obj["LastModified"].isoformat(),
                        "size": obj["Size"],
                    }
                )

            # Sort by last modified (newest first)
            backups.sort(key=lambda x: x["last_modified"], reverse=True)

            return backups

        except Exception as e:
            logger.error(f"Failed to list backups: {str(e)}")
            return []

    async def restore_database(self, backup_key: str, restore_path: Path) -> bool:
        """Restore database from S3 backup.

        Args:
            backup_key: S3 key of the backup to restore
            restore_path: Path where to restore the database

        Returns:
            True if restore successful, False otherwise
        """
        if not self.s3_config or not self.s3_config.enabled:
            logger.warning("S3 backup is not configured or disabled")
            return False

        try:
            s3_client = self._get_s3_client()

            # Download backup file
            logger.info(f"Starting database restore from S3: {backup_key}")

            # Create parent directory if it doesn't exist
            restore_path.parent.mkdir(parents=True, exist_ok=True)

            # Download to temporary file first, then move to final location
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                s3_client.download_file(
                    self.s3_config.bucket_name, backup_key, temp_file.name
                )

                # Move temp file to final location
                temp_path = Path(temp_file.name)
                temp_path.replace(restore_path)

            logger.info(f"Database restore completed successfully: {restore_path}")
            return True

        except Exception as e:
            logger.error(f"Database restore failed: {str(e)}")
            return False
