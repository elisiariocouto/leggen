"""Schema introspection helpers shared by migration steps.

Migrations must be safe to re-run: a database that predates version tracking
replays every step from 1, so each one guards itself with these checks rather
than assuming it has not run before.
"""

import sqlite3


def table_exists(cursor: sqlite3.Cursor, table: str) -> bool:
    """Return True if a table of this name exists."""
    cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cursor.fetchone() is not None


def column_names(cursor: sqlite3.Cursor, table: str) -> set[str]:
    """Return the column names of a table (empty if it does not exist)."""
    if not table_exists(cursor, table):
        return set()
    return {row[1] for row in cursor.execute(f"PRAGMA table_info({table})")}


def column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    """Return True if the table exists and has this column."""
    return column in column_names(cursor, table)


def add_column_if_missing(
    cursor: sqlite3.Cursor, table: str, column: str, declaration: str
) -> bool:
    """Add a column unless the table lacks existence or already has it.

    Returns True when the ALTER actually ran. The table name and declaration
    are interpolated because SQLite does not accept bound parameters in DDL;
    both are migration-authored constants, never user input.
    """
    if not table_exists(cursor, table) or column_exists(cursor, table, column):
        return False
    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")
    return True
