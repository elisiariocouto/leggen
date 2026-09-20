"""Centralized path management for Leggen."""

import contextlib
import os
from pathlib import Path


class PathManager:
    """Manages configurable paths for config and database files."""

    def __init__(self):
        self._config_dir: Path | None = None
        self._database_path: Path | None = None

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

    def configured_database_path(self) -> Path | None:
        """The database path the user chose (flag or LEGGEN_DATABASE_PATH), or
        None when only the default would apply."""
        if self._database_path is not None:
            return self._database_path
        database_path = os.environ.get("LEGGEN_DATABASE_PATH")
        return Path(database_path) if database_path else None

    def get_database_path(self) -> Path:
        """Get the database file path and ensure the directory exists."""
        db_path = self.configured_database_path() or (
            self.get_config_dir() / "leggen.db"
        )

        # Try to ensure the directory exists, but handle permission errors gracefully
        with contextlib.suppress(PermissionError, OSError):
            db_path.parent.mkdir(parents=True, exist_ok=True)

        return db_path

    def set_database_path(self, path: Path) -> None:
        """Set the database file path."""
        self._database_path = Path(path)


# Global instance for the application
path_manager = PathManager()
