import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from leggen.utils.paths import path_manager


def create_connection(
    db_path: Path | None = None, row_factory: bool = False
) -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys, WAL mode, and a busy timeout set.

    Every connection in the codebase must go through here — foreign_keys is
    per-connection in SQLite, so a single raw sqlite3.connect() silently
    disables ON DELETE CASCADE for that connection.
    """
    if db_path is None:
        db_path = path_manager.get_database_path()
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    if row_factory:
        conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db_connection(row_factory: bool = False) -> Generator[sqlite3.Connection]:
    """Context manager for database connections with proper cleanup."""
    conn = create_connection(row_factory=row_factory)
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def db_exists() -> bool:
    """Check if database file exists."""
    db_path = path_manager.get_database_path()
    return db_path.exists()
