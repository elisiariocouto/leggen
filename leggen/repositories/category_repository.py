"""Repository for transaction category data operations."""

from typing import Any, Optional

from leggen.repositories.db import db_exists, get_db_connection
from leggen.services.categorizer import extract_keywords

DEFAULT_CATEGORIES = [
    {"name": "Groceries", "color": "#22c55e", "icon": "shopping-cart"},
    {"name": "Transport", "color": "#3b82f6", "icon": "car"},
    {"name": "Salary", "color": "#a855f7", "icon": "banknote"},
    {"name": "Dining", "color": "#f97316", "icon": "utensils"},
    {"name": "Shopping", "color": "#ec4899", "icon": "shopping-bag"},
    {"name": "Utilities", "color": "#64748b", "icon": "zap"},
    {"name": "Entertainment", "color": "#eab308", "icon": "film"},
    {"name": "Healthcare", "color": "#ef4444", "icon": "heart-pulse"},
    {"name": "Transfer", "color": "#06b6d4", "icon": "arrow-right-left"},
    {"name": "Cash", "color": "#84cc16", "icon": "wallet"},
    {"name": "Subscriptions", "color": "#8b5cf6", "icon": "repeat"},
    {"name": "Other", "color": "#6b7280", "icon": "tag"},
]


class CategoryRepository:
    """Repository for category data operations."""

    def create_table(self) -> None:
        """Create category tables and seed defaults."""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT DEFAULT '#6b7280',
                    icon TEXT,
                    is_default BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transaction_categories (
                    accountId TEXT NOT NULL,
                    transactionId TEXT NOT NULL,
                    categoryId INTEGER NOT NULL,
                    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (accountId, transactionId),
                    FOREIGN KEY (categoryId) REFERENCES categories(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tc_category
                ON transaction_categories(categoryId)
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS category_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    categoryId INTEGER NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    UNIQUE(keyword, categoryId),
                    FOREIGN KEY (categoryId) REFERENCES categories(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ck_keyword
                ON category_keywords(keyword)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ck_category
                ON category_keywords(categoryId)
            """)

            # Seed default categories if empty
            cursor.execute("SELECT COUNT(*) FROM categories")
            if cursor.fetchone()[0] == 0:
                for cat in DEFAULT_CATEGORIES:
                    cursor.execute(
                        "INSERT INTO categories (name, color, icon, is_default) VALUES (?, ?, ?, 1)",
                        (cat["name"], cat["color"], cat["icon"]),
                    )

            conn.commit()

    # --- Category CRUD ---

    def get_all_categories(self) -> list[dict[str, Any]]:
        """Get all categories."""
        if not db_exists():
            return []

        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, color, icon, is_default, created_at FROM categories ORDER BY is_default DESC, name"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_category_by_id(self, category_id: int) -> Optional[dict[str, Any]]:
        """Get a category by ID."""
        if not db_exists():
            return None

        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, color, icon, is_default, created_at FROM categories WHERE id = ?",
                (category_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_category(
        self, name: str, color: str = "#6b7280", icon: Optional[str] = None
    ) -> dict[str, Any]:
        """Create a new custom category."""
        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO categories (name, color, icon, is_default) VALUES (?, ?, ?, 0)",
                (name, color, icon),
            )
            conn.commit()
            category_id = cursor.lastrowid
            cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            return dict(cursor.fetchone())

    def update_category(
        self,
        category_id: int,
        name: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
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

    def assign_category(
        self,
        account_id: str,
        transaction_id: str,
        category_id: int,
        description: str = "",
        creditor_name: str = "",
        debtor_name: str = "",
    ) -> None:
        """Assign a category to a transaction and learn keywords."""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check for existing assignment and unlearn old keywords
            cursor.execute(
                "SELECT categoryId FROM transaction_categories WHERE accountId = ? AND transactionId = ?",
                (account_id, transaction_id),
            )
            existing = cursor.fetchone()
            if existing:
                old_category_id = existing[0]
                self._unlearn_keywords_conn(
                    cursor, old_category_id, description, creditor_name, debtor_name
                )

            # Insert or replace assignment
            cursor.execute(
                """INSERT OR REPLACE INTO transaction_categories (accountId, transactionId, categoryId)
                   VALUES (?, ?, ?)""",
                (account_id, transaction_id, category_id),
            )

            # Learn keywords from this transaction
            self._learn_keywords_conn(
                cursor, category_id, description, creditor_name, debtor_name
            )

            conn.commit()

    def remove_category(
        self,
        account_id: str,
        transaction_id: str,
        description: str = "",
        creditor_name: str = "",
        debtor_name: str = "",
    ) -> bool:
        """Remove category from a transaction and unlearn keywords."""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get current assignment
            cursor.execute(
                "SELECT categoryId FROM transaction_categories WHERE accountId = ? AND transactionId = ?",
                (account_id, transaction_id),
            )
            existing = cursor.fetchone()
            if not existing:
                return False

            old_category_id = existing[0]
            self._unlearn_keywords_conn(
                cursor, old_category_id, description, creditor_name, debtor_name
            )

            cursor.execute(
                "DELETE FROM transaction_categories WHERE accountId = ? AND transactionId = ?",
                (account_id, transaction_id),
            )
            conn.commit()
            return True

    def get_transaction_category(
        self, account_id: str, transaction_id: str
    ) -> Optional[dict[str, Any]]:
        """Get the category assigned to a transaction."""
        if not db_exists():
            return None

        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT c.id, c.name, c.color, c.icon, c.is_default
                   FROM transaction_categories tc
                   JOIN categories c ON tc.categoryId = c.id
                   WHERE tc.accountId = ? AND tc.transactionId = ?""",
                (account_id, transaction_id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def bulk_assign_by_description(
        self,
        category_id: int,
        description: str,
    ) -> int:
        """Assign a category to all transactions matching the given description.

        Unlearns keywords for transactions that had a different category,
        learns keywords once for the new assignment, and returns the count
        of affected transactions.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Find all transactions with this exact description
            cursor.execute(
                "SELECT accountId, transactionId FROM transactions WHERE description = ?",
                (description,),
            )
            matching = cursor.fetchall()
            if not matching:
                return 0

            # Find distinct old categories that will be replaced
            placeholders = ",".join(["(?, ?)" for _ in matching])
            params_pairs = [val for row in matching for val in (row[0], row[1])]
            cursor.execute(
                f"""SELECT DISTINCT categoryId FROM transaction_categories
                    WHERE (accountId, transactionId) IN ({placeholders})
                    AND categoryId != ?""",
                [*params_pairs, category_id],
            )
            old_category_ids = [row[0] for row in cursor.fetchall()]

            # Unlearn keywords once per distinct old category
            for old_cat_id in old_category_ids:
                self._unlearn_keywords_conn(cursor, old_cat_id, description, "", "")

            # Batch insert/replace all assignments
            cursor.executemany(
                """INSERT OR REPLACE INTO transaction_categories (accountId, transactionId, categoryId)
                   VALUES (?, ?, ?)""",
                [(row[0], row[1], category_id) for row in matching],
            )

            # Learn keywords once for this bulk action
            self._learn_keywords_conn(cursor, category_id, description, "", "")

            conn.commit()
            return len(matching)

    def bulk_remove_by_description(self, description: str) -> int:
        """Remove category from all transactions matching the given description.

        Unlearns keywords once per distinct category being removed and
        returns the count of affected transactions.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Find all categorized transactions with this exact description
            cursor.execute(
                """SELECT tc.accountId, tc.transactionId, tc.categoryId
                   FROM transaction_categories tc
                   JOIN transactions t ON tc.accountId = t.accountId AND tc.transactionId = t.transactionId
                   WHERE t.description = ?""",
                (description,),
            )
            matching = cursor.fetchall()
            if not matching:
                return 0

            # Unlearn keywords once per distinct old category
            old_category_ids = {row[2] for row in matching}
            for old_cat_id in old_category_ids:
                self._unlearn_keywords_conn(cursor, old_cat_id, description, "", "")

            # Delete all assignments
            placeholders = ",".join(["(?, ?)" for _ in matching])
            params_pairs = [val for row in matching for val in (row[0], row[1])]
            cursor.execute(
                f"""DELETE FROM transaction_categories
                    WHERE (accountId, transactionId) IN ({placeholders})""",
                params_pairs,
            )

            conn.commit()
            return len(matching)

    # --- Keyword learning ---

    def _learn_keywords_conn(
        self,
        cursor: Any,
        category_id: int,
        description: str,
        creditor_name: str,
        debtor_name: str,
    ) -> None:
        """Learn keywords from transaction text fields (using existing cursor)."""
        text = f"{description} {creditor_name} {debtor_name}"
        keywords = extract_keywords(text)

        for keyword in keywords:
            cursor.execute(
                """INSERT INTO category_keywords (keyword, categoryId, frequency)
                   VALUES (?, ?, 1)
                   ON CONFLICT(keyword, categoryId) DO UPDATE SET frequency = frequency + 1""",
                (keyword, category_id),
            )

    def _unlearn_keywords_conn(
        self,
        cursor: Any,
        category_id: int,
        description: str,
        creditor_name: str,
        debtor_name: str,
    ) -> None:
        """Unlearn keywords from transaction text fields (using existing cursor)."""
        text = f"{description} {creditor_name} {debtor_name}"
        keywords = extract_keywords(text)

        for keyword in keywords:
            cursor.execute(
                "UPDATE category_keywords SET frequency = frequency - 1 WHERE keyword = ? AND categoryId = ?",
                (keyword, category_id),
            )

        # Clean up zero/negative frequency entries
        cursor.execute(
            "DELETE FROM category_keywords WHERE categoryId = ? AND frequency <= 0",
            (category_id,),
        )

    # --- Suggestion engine ---

    def suggest_category(
        self,
        description: str,
        creditor_name: str = "",
        debtor_name: str = "",
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Suggest categories based on keyword matching."""
        if not db_exists():
            return []

        text = f"{description} {creditor_name} {debtor_name}"
        keywords = extract_keywords(text)

        if not keywords:
            return []

        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()

            placeholders = ",".join("?" * len(keywords))
            cursor.execute(
                f"""SELECT c.id, c.name, c.color, c.icon, c.is_default,
                           SUM(ck.frequency) as score
                    FROM category_keywords ck
                    JOIN categories c ON ck.categoryId = c.id
                    WHERE ck.keyword IN ({placeholders})
                    GROUP BY ck.categoryId
                    ORDER BY score DESC
                    LIMIT ?""",
                [*keywords, limit],
            )

            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                score = row_dict.pop("score")
                confidence = "high" if score > 10 else "medium" if score >= 5 else "low"
                results.append(
                    {
                        "category": row_dict,
                        "score": score,
                        "confidence": confidence,
                    }
                )

            return results
