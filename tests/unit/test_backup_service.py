"""Tests for backup service functionality."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError, NoCredentialsError

from leggen.models.config import S3BackupConfig
from leggen.services.backup_service import BackupService


@pytest.mark.unit
class TestBackupService:
    """Test backup service functionality."""

    def test_backup_service_initialization(self):
        """Test backup service can be initialized."""
        service = BackupService()
        assert service.s3_config is None
        assert service._s3_client is None

    def test_backup_service_with_config(self):
        """Test backup service initialization with config."""
        s3_config = S3BackupConfig(
            access_key_id="test-key",
            secret_access_key="test-secret",
            bucket_name="test-bucket",
            region="us-east-1",
        )
        service = BackupService(s3_config)
        assert service.s3_config == s3_config

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """Test successful S3 connection test."""
        s3_config = S3BackupConfig(
            access_key_id="test-key",
            secret_access_key="test-secret",
            bucket_name="test-bucket",
            region="us-east-1",
        )

        service = BackupService()

        # Mock S3 client
        with patch("boto3.Session") as mock_session:
            mock_client = MagicMock()
            mock_session.return_value.client.return_value = mock_client

            # Mock successful list_objects_v2 call
            mock_client.list_objects_v2.return_value = {"Contents": []}

            result = await service.test_connection(s3_config)
            assert result is True

            # Verify the client was called correctly
            mock_client.list_objects_v2.assert_called_once_with(
                Bucket="test-bucket", MaxKeys=1
            )

    @pytest.mark.asyncio
    async def test_test_connection_no_credentials(self):
        """Test S3 connection test with no credentials."""
        s3_config = S3BackupConfig(
            access_key_id="test-key",
            secret_access_key="test-secret",
            bucket_name="test-bucket",
            region="us-east-1",
        )

        service = BackupService()

        # Mock S3 client to raise NoCredentialsError
        with patch("boto3.Session") as mock_session:
            mock_client = MagicMock()
            mock_session.return_value.client.return_value = mock_client
            mock_client.list_objects_v2.side_effect = NoCredentialsError()

            result = await service.test_connection(s3_config)
            assert result is False

    @pytest.mark.asyncio
    async def test_test_connection_client_error(self):
        """Test S3 connection test with client error."""
        s3_config = S3BackupConfig(
            access_key_id="test-key",
            secret_access_key="test-secret",
            bucket_name="test-bucket",
            region="us-east-1",
        )

        service = BackupService()

        # Mock S3 client to raise ClientError
        with patch("boto3.Session") as mock_session:
            mock_client = MagicMock()
            mock_session.return_value.client.return_value = mock_client
            error_response = {
                "Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}
            }
            mock_client.list_objects_v2.side_effect = ClientError(
                error_response, "ListObjectsV2"
            )

            result = await service.test_connection(s3_config)
            assert result is False

    @pytest.mark.asyncio
    async def test_backup_database_no_config(self):
        """Test backup database with no configuration."""
        service = BackupService()

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db_path.write_text("test database content")

            result = await service.backup_database(db_path)
            assert result is False

    @pytest.mark.asyncio
    async def test_backup_database_disabled(self):
        """Test backup database with disabled configuration."""
        s3_config = S3BackupConfig(
            access_key_id="test-key",
            secret_access_key="test-secret",
            bucket_name="test-bucket",
            region="us-east-1",
            enabled=False,
        )
        service = BackupService(s3_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db_path.write_text("test database content")

            result = await service.backup_database(db_path)
            assert result is False

    @pytest.mark.asyncio
    async def test_backup_database_file_not_found(self):
        """Test backup database with non-existent file."""
        s3_config = S3BackupConfig(
            access_key_id="test-key",
            secret_access_key="test-secret",
            bucket_name="test-bucket",
            region="us-east-1",
        )
        service = BackupService(s3_config)

        non_existent_path = Path("/non/existent/path.db")
        result = await service.backup_database(non_existent_path)
        assert result is False

    @pytest.mark.asyncio
    async def test_backup_database_success(self):
        """Test successful database backup uploads a sqlite snapshot."""
        s3_config = S3BackupConfig(
            access_key_id="test-key",
            secret_access_key="test-secret",
            bucket_name="test-bucket",
            region="us-east-1",
        )
        service = BackupService(s3_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
            conn.execute("INSERT INTO t VALUES (1)")
            conn.commit()
            conn.close()

            # Mock S3 client
            with patch("boto3.Session") as mock_session:
                mock_client = MagicMock()
                mock_session.return_value.client.return_value = mock_client

                uploaded = {}

                def capture_upload(source, bucket, key):
                    # The snapshot only exists during the call — verify it here
                    snapshot = sqlite3.connect(source)
                    uploaded["rows"] = snapshot.execute(
                        "SELECT COUNT(*) FROM t"
                    ).fetchone()[0]
                    snapshot.close()
                    uploaded["source"] = source
                    uploaded["bucket"] = bucket
                    uploaded["key"] = key

                mock_client.upload_file.side_effect = capture_upload

                result = await service.backup_database(db_path)
                assert result is True

                # A sqlite snapshot is uploaded, not the live file
                assert uploaded["source"] != str(db_path)
                assert uploaded["rows"] == 1
                assert uploaded["bucket"] == "test-bucket"
                assert uploaded["key"].startswith("leggen_backups/database_backup_")

    @pytest.mark.asyncio
    async def test_restore_database_rejects_foreign_key(self):
        """Restore refuses S3 keys outside the backup prefix."""
        s3_config = S3BackupConfig(
            access_key_id="test-key",
            secret_access_key="test-secret",
            bucket_name="test-bucket",
            region="us-east-1",
        )
        service = BackupService(s3_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            restore_path = Path(tmpdir) / "restored.db"
            with patch("boto3.Session") as mock_session:
                mock_client = MagicMock()
                mock_session.return_value.client.return_value = mock_client

                assert (
                    await service.restore_database("other/key.db", restore_path)
                    is False
                )
                assert (
                    await service.restore_database(
                        "leggen_backups/../secrets", restore_path
                    )
                    is False
                )
                mock_client.download_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_restore_database_success(self):
        """Restore downloads into the destination directory and swaps in place."""
        s3_config = S3BackupConfig(
            access_key_id="test-key",
            secret_access_key="test-secret",
            bucket_name="test-bucket",
            region="us-east-1",
        )
        service = BackupService(s3_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            restore_path = Path(tmpdir) / "restored.db"

            with patch("boto3.Session") as mock_session:
                mock_client = MagicMock()
                mock_session.return_value.client.return_value = mock_client

                def fake_download(bucket, key, dest):
                    # The temp file must live next to the final location so the
                    # rename never crosses filesystems
                    assert Path(dest).parent == restore_path.parent
                    Path(dest).write_text("db payload")

                mock_client.download_file.side_effect = fake_download

                result = await service.restore_database(
                    "leggen_backups/database_backup_x.db", restore_path
                )
                assert result is True
                assert restore_path.read_text() == "db payload"

    @pytest.mark.asyncio
    async def test_list_backups_success(self):
        """Test successful backup listing."""
        s3_config = S3BackupConfig(
            access_key_id="test-key",
            secret_access_key="test-secret",
            bucket_name="test-bucket",
            region="us-east-1",
        )
        service = BackupService(s3_config)

        # Mock S3 client response
        with patch("boto3.Session") as mock_session:
            mock_client = MagicMock()
            mock_session.return_value.client.return_value = mock_client

            from datetime import datetime

            mock_response = {
                "Contents": [
                    {
                        "Key": "leggen_backups/database_backup_20250101_120000.db",
                        "LastModified": datetime(2025, 1, 1, 12, 0, 0),
                        "Size": 1024,
                    },
                    {
                        "Key": "leggen_backups/database_backup_20250101_130000.db",
                        "LastModified": datetime(2025, 1, 1, 13, 0, 0),
                        "Size": 2048,
                    },
                ]
            }
            mock_client.list_objects_v2.return_value = mock_response

            backups = await service.list_backups()
            assert len(backups) == 2

            # Check that backups are sorted by last modified (newest first)
            assert backups[0]["last_modified"] > backups[1]["last_modified"]
            assert backups[0]["size"] == 2048
            assert backups[1]["size"] == 1024
