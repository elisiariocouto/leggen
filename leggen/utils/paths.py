"""Centralized path management for Leggen."""

import contextlib
import os
from pathlib import Path


def get_config_dir() -> Path:
    """Get the configuration directory.
    
    Priority:
    1. LEGGEN_CONFIG_DIR environment variable
    2. Default: ~/.config/leggen
    """
    config_dir = os.environ.get("LEGGEN_CONFIG_DIR")
    if config_dir:
        return Path(config_dir)
    return Path.home() / ".config" / "leggen"


def get_config_file_path() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.toml"


def get_database_path() -> Path:
    """Get the database file path and ensure the directory exists.
    
    Priority:
    1. LEGGEN_DATABASE_PATH environment variable
    2. Default: <config_dir>/leggen.db
    """
    database_path = os.environ.get("LEGGEN_DATABASE_PATH")
    db_path = Path(database_path) if database_path else get_config_dir() / "leggen.db"

    # Try to ensure the directory exists, but handle permission errors gracefully
    with contextlib.suppress(PermissionError, OSError):
        db_path.parent.mkdir(parents=True, exist_ok=True)

    return db_path


def get_auth_file_path() -> Path:
    """Get the authentication file path."""
    return get_config_dir() / "auth.json"


def ensure_config_dir_exists() -> None:
    """Ensure the configuration directory exists."""
    get_config_dir().mkdir(parents=True, exist_ok=True)


def ensure_database_dir_exists() -> None:
    """Ensure the database directory exists."""
    get_database_path().parent.mkdir(parents=True, exist_ok=True)
