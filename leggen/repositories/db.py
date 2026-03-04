import sqlite3
from collections.abc import Generator
from contextlib import contextmanager

from leggen.utils.paths import path_manager


@contextmanager
def get_db_connection(row_factory: bool = False) -> Generator[sqlite3.Connection]:
    """Context manager for database connections with proper cleanup."""
    db_path = path_manager.get_database_path()
    conn = sqlite3.connect(str(db_path))
    if row_factory:
        conn.row_factory = sqlite3.Row
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
