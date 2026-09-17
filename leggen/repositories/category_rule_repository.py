"""Repository for category rules and the assignments they make."""

import sqlite3
from typing import Any

from leggen.errors import CategoryRuleExistsError
from leggen.repositories.db import db_exists, get_db_connection

_RULE_COLUMNS = (
    "id, name, description, categoryId, lua_script, priority, is_active,"
    " is_default, exclude_from_stats, created_at, updated_at"
)

# Fields a caller may set; anything else on the row is bookkeeping.
_EDITABLE = frozenset(
    {
        "name",
        "description",
        "categoryId",
        "lua_script",
        "priority",
        "is_active",
        "is_default",
        "exclude_from_stats",
    }
)


def _row_to_rule(row: sqlite3.Row) -> dict[str, Any]:
    rule = dict(row)
    # SQLite stores booleans as 0/1; hand back real booleans (the nullable
    # exclusion flag keeps None).
    rule["is_active"] = bool(rule["is_active"])
    rule["is_default"] = bool(rule["is_default"])
    if rule["exclude_from_stats"] is not None:
        rule["exclude_from_stats"] = bool(rule["exclude_from_stats"])
    return rule


class CategoryRuleRepository:
    """CRUD for category_rules, plus the rule-made rows in transaction_categories."""

    # --- Rules ---

    def get_all_rules(self, active_only: bool = False) -> list[dict[str, Any]]:
        """Rules in evaluation order: priority ascending, then id."""
        if not db_exists():
            return []
        where = " WHERE is_active = 1" if active_only else ""
        with get_db_connection(row_factory=True) as conn:
            rows = conn.execute(
                f"SELECT {_RULE_COLUMNS} FROM category_rules{where}"
                " ORDER BY priority, id"
            ).fetchall()
            return [_row_to_rule(row) for row in rows]

    def get_rule_by_id(self, rule_id: int) -> dict[str, Any] | None:
        if not db_exists():
            return None
        with get_db_connection(row_factory=True) as conn:
            row = conn.execute(
                f"SELECT {_RULE_COLUMNS} FROM category_rules WHERE id = ?", (rule_id,)
            ).fetchone()
            return _row_to_rule(row) if row else None

    def get_rule_by_name(self, name: str) -> dict[str, Any] | None:
        if not db_exists():
            return None
        with get_db_connection(row_factory=True) as conn:
            row = conn.execute(
                f"SELECT {_RULE_COLUMNS} FROM category_rules WHERE name = ?", (name,)
            ).fetchone()
            return _row_to_rule(row) if row else None

    def create_rule(
        self,
        name: str,
        category_id: int,
        lua_script: str,
        description: str | None = None,
        priority: int = 100,
        is_active: bool = True,
        is_default: bool = False,
        exclude_from_stats: bool | None = None,
    ) -> dict[str, Any]:
        """Create a rule.

        Raises CategoryRuleExistsError when the name is taken. A missing
        category surfaces as sqlite3.IntegrityError, which callers validate
        against beforehand.
        """
        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """INSERT INTO category_rules
                       (name, description, categoryId, lua_script, priority,
                        is_active, is_default, exclude_from_stats)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        name,
                        description,
                        category_id,
                        lua_script,
                        priority,
                        is_active,
                        is_default,
                        exclude_from_stats,
                    ),
                )
            except sqlite3.IntegrityError as e:
                if "UNIQUE" in str(e):
                    raise CategoryRuleExistsError(
                        f"Category rule '{name}' already exists."
                    ) from e
                raise
            conn.commit()
            row = cursor.execute(
                f"SELECT {_RULE_COLUMNS} FROM category_rules WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
            return _row_to_rule(row)

    def update_rule(self, rule_id: int, **fields: Any) -> dict[str, Any] | None:
        """Update the given fields. Returns the rule, or None if it does not exist.

        Pass a field explicitly as None to clear it (description,
        exclude_from_stats); leave it out to keep the stored value.
        """
        unknown = set(fields) - _EDITABLE
        if unknown:
            raise ValueError(f"Not editable: {sorted(unknown)}")
        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()
            if fields:
                assignments = ", ".join(f"{column} = ?" for column in fields)
                try:
                    cursor.execute(
                        f"""UPDATE category_rules
                            SET {assignments}, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?""",
                        [*fields.values(), rule_id],
                    )
                except sqlite3.IntegrityError as e:
                    if "UNIQUE" in str(e):
                        raise CategoryRuleExistsError(
                            f"Category rule '{fields.get('name')}' already exists."
                        ) from e
                    raise
                conn.commit()
            row = cursor.execute(
                f"SELECT {_RULE_COLUMNS} FROM category_rules WHERE id = ?", (rule_id,)
            ).fetchone()
            return _row_to_rule(row) if row else None

    def delete_rule(self, rule_id: int) -> bool:
        """Delete a rule. Its assignments go with it (ON DELETE CASCADE)."""
        with get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM category_rules WHERE id = ?", (rule_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- Rule-made assignments ---

    def apply_assignments(
        self, assignments: list[tuple[str, str, int, int, bool | None]]
    ) -> int:
        """Record rule-made category assignments.

        Each entry is (account_id, transaction_id, category_id, rule_id,
        exclude_from_stats). A manual assignment on the same transaction is
        left untouched: the engine only ever writes over its own rows.
        Returns how many rows were written.
        """
        if not assignments:
            return 0
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """INSERT INTO transaction_categories
                   (accountId, transactionId, categoryId, source, ruleId, exclude_from_stats)
                   VALUES (?, ?, ?, 'rule', ?, ?)
                   ON CONFLICT(accountId, transactionId) DO UPDATE SET
                       categoryId = excluded.categoryId,
                       ruleId = excluded.ruleId,
                       exclude_from_stats = excluded.exclude_from_stats,
                       assigned_at = CURRENT_TIMESTAMP
                   WHERE transaction_categories.source = 'rule'""",
                assignments,
            )
            conn.commit()
            return cursor.rowcount if cursor.rowcount >= 0 else len(assignments)

    def clear_assignments(self, keys: list[tuple[str, str]]) -> int:
        """Remove rule-made assignments for the given (account_id, transaction_id)
        keys — when no active rule matches them any more. Manual rows stay."""
        if not keys:
            return 0
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """DELETE FROM transaction_categories
                   WHERE accountId = ? AND transactionId = ? AND source = 'rule'""",
                keys,
            )
            conn.commit()
            return cursor.rowcount if cursor.rowcount >= 0 else len(keys)
