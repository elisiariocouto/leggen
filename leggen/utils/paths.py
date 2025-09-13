"""Centralized path management for Leggen."""

import contextlib
import os
from pathlib import Path
from typing import Optional


class PathManager:
    """Manages configurable paths for config and database files."""

    def __init__(self):
        self._config_dir: Optional[Path] = None
        self._database_path: Optional[Path] = None

    def get_config_dir(self) -> Path:
        """Get the configuration directory."""
        if self._config_dir is not None:
            return self._config_dir

        # Check environment variable first
        config_dir = os.environ.get("LEGGEN_CONFIG_DIR")
        if config_dir:
            return Path(config_dir)

        # Default to ~/.config/leggen
        return Path.home() / ".config" / "leggen"

    def set_config_dir(self, path: Path) -> None:
        """Set the configuration directory."""
        self._config_dir = Path(path)

    def get_config_file_path(self) -> Path:
        """Get the configuration file path."""
        return self.get_config_dir() / "config.toml"

    def get_database_path(self) -> Path:
        """Get the database file path and ensure the directory exists."""
        if self._database_path is not None:
            db_path = self._database_path
        else:
            # Check environment variable first
            database_path = os.environ.get("LEGGEN_DATABASE_PATH")
            if database_path:
                db_path = Path(database_path)
            else:
                # Default to config_dir/leggen.db
                db_path = self.get_config_dir() / "leggen.db"

        # Try to ensure the directory exists, but handle permission errors gracefully
        with contextlib.suppress(PermissionError, OSError):
            db_path.parent.mkdir(parents=True, exist_ok=True)

        return db_path

    def set_database_path(self, path: Path) -> None:
        """Set the database file path."""
        self._database_path = Path(path)

    def get_auth_file_path(self) -> Path:
        """Get the authentication file path."""
        return self.get_config_dir() / "auth.json"

    def ensure_config_dir_exists(self) -> None:
        """Ensure the configuration directory exists."""
        self.get_config_dir().mkdir(parents=True, exist_ok=True)

    def ensure_database_dir_exists(self) -> None:
        """Ensure the database directory exists.

        Note: get_database_path() now automatically ensures the directory exists,
        so this method is mainly for explicit directory creation in tests.
        """
        self.get_database_path().parent.mkdir(parents=True, exist_ok=True)


# Global instance for the application
path_manager = PathManager()
