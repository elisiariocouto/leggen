"""Repository for transaction category data operations."""

import sqlite3
from typing import Any

from leggen.errors import CategoryExistsError
from leggen.repositories.db import db_exists, get_db_connection


class CategoryRepository:
    """Repository for category data operations."""

    # --- Category CRUD ---

    def get_all_categories(self) -> list[dict[str, Any]]:
        """Get all categories."""
        if not db_exists():
            return []

        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, color, icon, is_default, exclude_from_stats, created_at FROM categories ORDER BY is_default DESC, name"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_category_by_id(self, category_id: int) -> dict[str, Any] | None:
        """Get a category by ID."""
        if not db_exists():
            return None

        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, color, icon, is_default, exclude_from_stats, created_at FROM categories WHERE id = ?",
                (category_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_category(
        self,
        name: str,
        color: str = "#6b7280",
        icon: str | None = None,
        exclude_from_stats: bool = False,
    ) -> dict[str, Any]:
        """Create a new custom category.

        Raises:
            ConflictError: If a category with this name already exists. The
                name is unique in the domain, not just in the schema, so the
                IntegrityError is translated rather than surfaced verbatim.
        """
        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO categories (name, color, icon, is_default, exclude_from_stats) VALUES (?, ?, ?, 0, ?)",
                    (name, color, icon, exclude_from_stats),
                )
            except sqlite3.IntegrityError as e:
                raise CategoryExistsError(f"Category '{name}' already exists.") from e
            conn.commit()
            category_id = cursor.lastrowid
            cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            return dict(cursor.fetchone())

    def update_category(
        self,
        category_id: int,
        name: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        exclude_from_stats: bool | None = None,
    ) -> dict[str, Any] | None:
        """Update a category."""
        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()

            updates = []
            params: list[Any] = []
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if color is not None:
                updates.append("color = ?")
                params.append(color)
            if icon is not None:
                updates.append("icon = ?")
                params.append(icon)
            if exclude_from_stats is not None:
                updates.append("exclude_from_stats = ?")
                params.append(exclude_from_stats)

            if not updates:
                return self.get_category_by_id(category_id)

            params.append(category_id)
            cursor.execute(
                f"UPDATE categories SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()

            cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_category(self, category_id: int) -> bool:
        """Delete a category. Returns True if deleted."""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if it's a default category
            cursor.execute(
                "SELECT is_default FROM categories WHERE id = ?", (category_id,)
            )
            row = cursor.fetchone()
            if not row:
                return False
            if row[0]:
                return False  # Cannot delete default categories

            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- Transaction-Category assignment ---

    # A manual choice replaces whatever a rule decided: the row becomes
    # manual, drops the rule reference and the rule's statistics flag, and
    # the engine leaves it alone from then on.
    _ASSIGN_SQL = """INSERT INTO transaction_categories
           (accountId, transactionId, categoryId, source, ruleId, exclude_from_stats)
           VALUES (?, ?, ?, 'manual', NULL, NULL)
           ON CONFLICT(accountId, transactionId) DO UPDATE SET
               categoryId = excluded.categoryId,
               source = 'manual',
               ruleId = NULL,
               exclude_from_stats = NULL,
               assigned_at = CURRENT_TIMESTAMP"""

    def assign_category(
        self, account_id: str, transaction_id: str, category_id: int
    ) -> None:
        """Assign a category to a transaction by hand."""
        with get_db_connection() as conn:
            conn.execute(self._ASSIGN_SQL, (account_id, transaction_id, category_id))
            conn.commit()

    def remove_category(self, account_id: str, transaction_id: str) -> bool:
        """Remove a transaction's category. Returns False if it had none."""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM transaction_categories WHERE accountId = ? AND transactionId = ?",
                (account_id, transaction_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def bulk_assign_by_description(self, category_id: int, description: str) -> int:
        """Assign a category to every transaction with exactly this description.

        Returns the number of transactions affected.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT accountId, transactionId FROM transactions WHERE description = ?",
                (description,),
            )
            matching = cursor.fetchall()
            if not matching:
                return 0
            cursor.executemany(
                self._ASSIGN_SQL,
                [(row[0], row[1], category_id) for row in matching],
            )
            conn.commit()
            return len(matching)

    def bulk_remove_by_description(self, description: str) -> int:
        """Remove the category from every transaction with exactly this
        description. Returns the number of transactions affected."""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """DELETE FROM transaction_categories
                   WHERE (accountId, transactionId) IN (
                       SELECT accountId, transactionId FROM transactions WHERE description = ?
                   )""",
                (description,),
            )
            conn.commit()
            return cursor.rowcount
