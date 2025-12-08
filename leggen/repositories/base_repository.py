import sqlite3
from contextlib import contextmanager

from leggen.utils.paths import path_manager


class BaseRepository:
    """Base repository with shared database connection logic"""

    @contextmanager
    def _get_db_connection(self, row_factory: bool = False):
        """Context manager for database connections with proper cleanup"""
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

    def _db_exists(self) -> bool:
        """Check if database file exists"""
        db_path = path_manager.get_database_path()
        return db_path.exists()
