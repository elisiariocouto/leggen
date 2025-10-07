"""Database helper utilities for Leggen - Compatibility layer."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from loguru import logger


@contextmanager
def get_db_connection(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections.

    Usage:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(...)
            conn.commit()
    """
    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def execute_query(
    db_path: Path, query: str, params: tuple = ()
) -> list[dict[str, Any]]:
    """Execute a SELECT query and return results as list of dicts."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def execute_single(
    db_path: Path, query: str, params: tuple = ()
) -> dict[str, Any] | None:
    """Execute a SELECT query and return a single result as dict or None."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None


def execute_count(db_path: Path, query: str, params: tuple = ()) -> int:
    """Execute a COUNT query and return the integer result."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else 0
