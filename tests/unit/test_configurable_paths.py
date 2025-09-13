"""Integration tests for configurable paths."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from leggen.utils.paths import path_manager
from leggen.database.sqlite import persist_balances, get_balances


class MockContext:
    """Mock context for testing."""

    pass


@pytest.mark.unit
class TestConfigurablePaths:
    """Test configurable path management."""

    def test_default_paths(self):
        """Test that default paths are correctly set."""
        # Reset path manager
        original_config = path_manager._config_dir
        original_db = path_manager._database_path

        try:
            path_manager._config_dir = None
            path_manager._database_path = None

            # Test defaults
            config_dir = path_manager.get_config_dir()
            db_path = path_manager.get_database_path()

            assert config_dir == Path.home() / ".config" / "leggen"
            assert db_path == Path.home() / ".config" / "leggen" / "leggen.db"
        finally:
            path_manager._config_dir = original_config
            path_manager._database_path = original_db

    def test_environment_variables(self):
        """Test that environment variables override defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_config_dir = Path(tmpdir) / "test-config"
            test_db_path = Path(tmpdir) / "test.db"

            with patch.dict(
                os.environ,
                {
                    "LEGGEN_CONFIG_DIR": str(test_config_dir),
                    "LEGGEN_DATABASE_PATH": str(test_db_path),
                },
            ):
                # Reset path manager to pick up environment variables
                original_config = path_manager._config_dir
                original_db = path_manager._database_path

                try:
                    path_manager._config_dir = None
                    path_manager._database_path = None

                    config_dir = path_manager.get_config_dir()
                    db_path = path_manager.get_database_path()

                    assert config_dir == test_config_dir
                    assert db_path == test_db_path
                finally:
                    path_manager._config_dir = original_config
                    path_manager._database_path = original_db

    def test_explicit_path_setting(self):
        """Test explicitly setting paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_config_dir = Path(tmpdir) / "explicit-config"
            test_db_path = Path(tmpdir) / "explicit.db"

            # Save original paths
            original_config = path_manager._config_dir
            original_db = path_manager._database_path

            try:
                # Set explicit paths
                path_manager.set_config_dir(test_config_dir)
                path_manager.set_database_path(test_db_path)

                assert path_manager.get_config_dir() == test_config_dir
                assert path_manager.get_database_path() == test_db_path
                assert (
                    path_manager.get_config_file_path()
                    == test_config_dir / "config.toml"
                )
                assert (
                    path_manager.get_auth_file_path() == test_config_dir / "auth.json"
                )
            finally:
                # Restore original paths
                path_manager._config_dir = original_config
                path_manager._database_path = original_db

    def test_database_operations_with_custom_path(self):
        """Test that database operations work with custom paths."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            test_db_path = Path(tmp_file.name)

        # Save original database path
        original_db = path_manager._database_path

        try:
            # Set custom database path
            path_manager.set_database_path(test_db_path)

            # Test database operations
            ctx = MockContext()
            balance = {
                "account_id": "test-account",
                "bank": "TEST_BANK",
                "status": "active",
                "iban": "TEST_IBAN",
                "amount": 1000.0,
                "currency": "EUR",
                "type": "available",
                "timestamp": "2023-01-01T00:00:00",
            }

            # Persist balance
            persist_balances(ctx, balance)

            # Retrieve balances
            balances = get_balances()

            assert len(balances) == 1
            assert balances[0]["account_id"] == "test-account"
            assert balances[0]["amount"] == 1000.0

            # Verify database file exists at custom location
            assert test_db_path.exists()

        finally:
            # Restore original path and cleanup
            path_manager._database_path = original_db
            if test_db_path.exists():
                test_db_path.unlink()

    def test_directory_creation(self):
        """Test that directories are created as needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_config_dir = Path(tmpdir) / "new" / "config" / "dir"
            test_db_path = Path(tmpdir) / "new" / "db" / "dir" / "test.db"

            # Save original paths
            original_config = path_manager._config_dir
            original_db = path_manager._database_path

            try:
                # Set paths to non-existent directories
                path_manager.set_config_dir(test_config_dir)
                path_manager.set_database_path(test_db_path)

                # Ensure directories are created
                path_manager.ensure_config_dir_exists()
                path_manager.ensure_database_dir_exists()

                assert test_config_dir.exists()
                assert test_db_path.parent.exists()

            finally:
                # Restore original paths
                path_manager._config_dir = original_config
                path_manager._database_path = original_db
