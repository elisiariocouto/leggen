"""Integration tests for configurable paths."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from leggen.services.database_service import DatabaseService
from leggen.utils import paths


@pytest.mark.unit
class TestConfigurablePaths:
    """Test configurable path management."""

    def test_default_paths(self):
        """Test that default paths are correctly set."""
        # Clear environment variables to test defaults
        with patch.dict(os.environ, {}, clear=True):
            config_dir = paths.get_config_dir()
            db_path = paths.get_database_path()

            assert config_dir == Path.home() / ".config" / "leggen"
            assert db_path == Path.home() / ".config" / "leggen" / "leggen.db"

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
                config_dir = paths.get_config_dir()
                db_path = paths.get_database_path()

                assert config_dir == test_config_dir
                assert db_path == test_db_path

    def test_explicit_path_setting(self):
        """Test explicitly setting paths via environment variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_config_dir = Path(tmpdir) / "explicit-config"
            test_db_path = Path(tmpdir) / "explicit.db"

            # Set paths via environment variables
            with patch.dict(
                os.environ,
                {
                    "LEGGEN_CONFIG_DIR": str(test_config_dir),
                    "LEGGEN_DATABASE_PATH": str(test_db_path),
                },
            ):
                assert paths.get_config_dir() == test_config_dir
                assert paths.get_database_path() == test_db_path
                assert (
                    paths.get_config_file_path() == test_config_dir / "config.toml"
                )
                assert paths.get_auth_file_path() == test_config_dir / "auth.json"

    def test_database_operations_with_custom_path(self):
        """Test that database operations work with custom paths."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            test_db_path = Path(tmp_file.name)

        try:
            # Set custom database path via environment variable
            with patch.dict(
                os.environ, {"LEGGEN_DATABASE_PATH": str(test_db_path)}
            ):
                # Test database operations using DatabaseService
                database_service = DatabaseService()
                balance_data = {
                    "balances": [
                        {
                            "balanceAmount": {"amount": "1000.0", "currency": "EUR"},
                            "balanceType": "available",
                        }
                    ],
                    "institution_id": "TEST_BANK",
                    "account_status": "active",
                    "iban": "TEST_IBAN",
                }

                # Use the internal balance persistence method since the test needs direct database access
                import asyncio

                asyncio.run(
                    database_service._persist_balance_sqlite("test-account", balance_data)
                )

                # Retrieve balances
                balances = asyncio.run(
                    database_service.get_balances_from_db("test-account")
                )

                assert len(balances) == 1
                assert balances[0]["account_id"] == "test-account"
                assert balances[0]["amount"] == 1000.0

                # Verify database file exists at custom location
                assert test_db_path.exists()

        finally:
            # Cleanup
            if test_db_path.exists():
                test_db_path.unlink()

    def test_directory_creation(self):
        """Test that directories are created as needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_config_dir = Path(tmpdir) / "new" / "config" / "dir"
            test_db_path = Path(tmpdir) / "new" / "db" / "dir" / "test.db"

            # Set paths via environment variables
            with patch.dict(
                os.environ,
                {
                    "LEGGEN_CONFIG_DIR": str(test_config_dir),
                    "LEGGEN_DATABASE_PATH": str(test_db_path),
                },
            ):
                # Ensure directories are created
                paths.ensure_config_dir_exists()
                paths.ensure_database_dir_exists()

                assert test_config_dir.exists()
                assert test_db_path.parent.exists()
