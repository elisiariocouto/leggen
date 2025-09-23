"""Tests for backup API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest

from leggen.api.models.backup import BackupSettings, S3Config
from leggen.models.config import S3BackupConfig


@pytest.mark.api
class TestBackupAPI:
    """Test backup-related API endpoints."""

    def test_get_backup_settings_no_config(self, api_client, mock_config):
        """Test getting backup settings with no configuration."""
        # Mock empty backup config by updating the config dict
        mock_config._config["backup"] = {}
        
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/backup/settings")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["s3"] is None

    def test_get_backup_settings_with_s3_config(self, api_client, mock_config):
        """Test getting backup settings with S3 configuration."""
        # Mock S3 backup config (with masked credentials)
        mock_config._config["backup"] = {
            "s3": {
                "access_key_id": "AKIATEST123",
                "secret_access_key": "secret123",
                "bucket_name": "test-bucket",
                "region": "us-east-1",
                "endpoint_url": None,
                "path_style": False,
                "enabled": True,
            }
        }
        
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/backup/settings")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["s3"] is not None
        
        s3_config = data["data"]["s3"]
        assert s3_config["access_key_id"] == "***"  # Masked
        assert s3_config["secret_access_key"] == "***"  # Masked
        assert s3_config["bucket_name"] == "test-bucket"
        assert s3_config["region"] == "us-east-1"
        assert s3_config["enabled"] is True

    @patch("leggen.services.backup_service.BackupService.test_connection")
    def test_update_backup_settings_success(self, mock_test_connection, api_client, mock_config):
        """Test successful backup settings update."""
        mock_test_connection.return_value = True
        mock_config._config["backup"] = {}
        
        request_data = {
            "s3": {
                "access_key_id": "AKIATEST123",
                "secret_access_key": "secret123",
                "bucket_name": "test-bucket",
                "region": "us-east-1",
                "endpoint_url": None,
                "path_style": False,
                "enabled": True,
            }
        }
        
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.put("/api/v1/backup/settings", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["updated"] is True
        
        # Verify connection test was called
        mock_test_connection.assert_called_once()

    @patch("leggen.services.backup_service.BackupService.test_connection")
    def test_update_backup_settings_connection_failure(self, mock_test_connection, api_client, mock_config):
        """Test backup settings update with connection test failure."""
        mock_test_connection.return_value = False
        mock_config._config["backup"] = {}
        
        request_data = {
            "s3": {
                "access_key_id": "AKIATEST123",
                "secret_access_key": "secret123",
                "bucket_name": "invalid-bucket",
                "region": "us-east-1",
                "endpoint_url": None,
                "path_style": False,
                "enabled": True,
            }
        }
        
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.put("/api/v1/backup/settings", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "S3 connection test failed" in data["detail"]

    @patch("leggen.services.backup_service.BackupService.test_connection")
    def test_test_backup_connection_success(self, mock_test_connection, api_client):
        """Test successful backup connection test."""
        mock_test_connection.return_value = True
        
        request_data = {
            "service": "s3",
            "config": {
                "access_key_id": "AKIATEST123",
                "secret_access_key": "secret123",
                "bucket_name": "test-bucket",
                "region": "us-east-1",
                "endpoint_url": None,
                "path_style": False,
                "enabled": True,
            }
        }
        
        response = api_client.post("/api/v1/backup/test", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["connected"] is True
        
        # Verify connection test was called
        mock_test_connection.assert_called_once()

    @patch("leggen.services.backup_service.BackupService.test_connection")
    def test_test_backup_connection_failure(self, mock_test_connection, api_client):
        """Test failed backup connection test."""
        mock_test_connection.return_value = False
        
        request_data = {
            "service": "s3",
            "config": {
                "access_key_id": "AKIATEST123",
                "secret_access_key": "secret123",
                "bucket_name": "invalid-bucket",
                "region": "us-east-1",
                "endpoint_url": None,
                "path_style": False,
                "enabled": True,
            }
        }
        
        response = api_client.post("/api/v1/backup/test", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_test_backup_connection_invalid_service(self, api_client):
        """Test backup connection test with invalid service."""
        request_data = {
            "service": "invalid",
            "config": {
                "access_key_id": "AKIATEST123",
                "secret_access_key": "secret123",
                "bucket_name": "test-bucket",
                "region": "us-east-1",
                "endpoint_url": None,
                "path_style": False,
                "enabled": True,
            }
        }
        
        response = api_client.post("/api/v1/backup/test", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Only 's3' service is supported" in data["detail"]

    @patch("leggen.services.backup_service.BackupService.list_backups")
    def test_list_backups_success(self, mock_list_backups, api_client, mock_config):
        """Test successful backup listing."""
        mock_list_backups.return_value = [
            {
                "key": "leggen_backups/database_backup_20250101_120000.db",
                "last_modified": "2025-01-01T12:00:00",
                "size": 1024,
            },
            {
                "key": "leggen_backups/database_backup_20250101_110000.db",
                "last_modified": "2025-01-01T11:00:00",
                "size": 512,
            },
        ]
        
        mock_config._config["backup"] = {
            "s3": {
                "access_key_id": "AKIATEST123",
                "secret_access_key": "secret123",
                "bucket_name": "test-bucket",
                "region": "us-east-1",
                "enabled": True,
            }
        }
        
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/backup/list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["key"] == "leggen_backups/database_backup_20250101_120000.db"

    def test_list_backups_no_config(self, api_client, mock_config):
        """Test backup listing with no configuration."""
        mock_config._config["backup"] = {}
        
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/backup/list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    @patch("leggen.services.backup_service.BackupService.backup_database")
    @patch("leggen.utils.paths.path_manager.get_database_path")
    def test_backup_operation_success(self, mock_get_db_path, mock_backup_db, api_client, mock_config):
        """Test successful backup operation."""
        from pathlib import Path
        
        mock_get_db_path.return_value = Path("/test/database.db")
        mock_backup_db.return_value = True
        
        mock_config._config["backup"] = {
            "s3": {
                "access_key_id": "AKIATEST123",
                "secret_access_key": "secret123",
                "bucket_name": "test-bucket",
                "region": "us-east-1",
                "enabled": True,
            }
        }
        
        request_data = {"operation": "backup"}
        
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.post("/api/v1/backup/operation", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["operation"] == "backup"
        assert data["data"]["completed"] is True
        
        # Verify backup was called
        mock_backup_db.assert_called_once()

    def test_backup_operation_no_config(self, api_client, mock_config):
        """Test backup operation with no configuration."""
        mock_config._config["backup"] = {}
        
        request_data = {"operation": "backup"}
        
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.post("/api/v1/backup/operation", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "S3 backup is not configured" in data["detail"]

    def test_backup_operation_invalid_operation(self, api_client, mock_config):
        """Test backup operation with invalid operation type."""
        mock_config._config["backup"] = {
            "s3": {
                "access_key_id": "AKIATEST123",
                "secret_access_key": "secret123",
                "bucket_name": "test-bucket",
                "region": "us-east-1",
                "enabled": True,
            }
        }
        
        request_data = {"operation": "invalid"}
        
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.post("/api/v1/backup/operation", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid operation" in data["detail"]