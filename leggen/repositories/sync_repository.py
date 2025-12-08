import json
import sqlite3
from typing import Any, Dict, List

from loguru import logger

from leggen.repositories.base_repository import BaseRepository
from leggen.utils.paths import path_manager


class SyncRepository(BaseRepository):
    """Repository for sync operation data"""

    def create_table(self):
        """Create sync_operations table with indexes"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at DATETIME NOT NULL,
                    completed_at DATETIME,
                    success BOOLEAN,
                    accounts_processed INTEGER DEFAULT 0,
                    transactions_added INTEGER DEFAULT 0,
                    transactions_updated INTEGER DEFAULT 0,
                    balances_updated INTEGER DEFAULT 0,
                    duration_seconds REAL,
                    errors TEXT,
                    logs TEXT,
                    trigger_type TEXT DEFAULT 'manual'
                )
            """)

            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sync_operations_started_at ON sync_operations(started_at)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sync_operations_success ON sync_operations(success)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sync_operations_trigger_type ON sync_operations(trigger_type)"
            )

            conn.commit()

    def persist(self, sync_operation: Dict[str, Any]) -> int:
        """Persist sync operation to database and return the ID"""
        try:
            self.create_table()

            db_path = path_manager.get_database_path()
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute(
                """INSERT INTO sync_operations (
                    started_at, completed_at, success, accounts_processed,
                    transactions_added, transactions_updated, balances_updated,
                    duration_seconds, errors, logs, trigger_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    sync_operation.get("started_at"),
                    sync_operation.get("completed_at"),
                    sync_operation.get("success"),
                    sync_operation.get("accounts_processed", 0),
                    sync_operation.get("transactions_added", 0),
                    sync_operation.get("transactions_updated", 0),
                    sync_operation.get("balances_updated", 0),
                    sync_operation.get("duration_seconds"),
                    json.dumps(sync_operation.get("errors", [])),
                    json.dumps(sync_operation.get("logs", [])),
                    sync_operation.get("trigger_type", "manual"),
                ),
            )

            operation_id = cursor.lastrowid
            if operation_id is None:
                raise ValueError("Failed to get operation ID after insert")

            conn.commit()
            conn.close()

            logger.debug(f"Persisted sync operation with ID: {operation_id}")
            return operation_id

        except Exception as e:
            logger.error(f"Failed to persist sync operation: {e}")
            raise

    def get_operations(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get sync operations from database"""
        try:
            db_path = path_manager.get_database_path()
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute(
                """SELECT id, started_at, completed_at, success, accounts_processed,
                          transactions_added, transactions_updated, balances_updated,
                          duration_seconds, errors, logs, trigger_type
                   FROM sync_operations
                   ORDER BY started_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            )

            operations = []
            for row in cursor.fetchall():
                operation = {
                    "id": row[0],
                    "started_at": row[1],
                    "completed_at": row[2],
                    "success": bool(row[3]) if row[3] is not None else None,
                    "accounts_processed": row[4],
                    "transactions_added": row[5],
                    "transactions_updated": row[6],
                    "balances_updated": row[7],
                    "duration_seconds": row[8],
                    "errors": json.loads(row[9]) if row[9] else [],
                    "logs": json.loads(row[10]) if row[10] else [],
                    "trigger_type": row[11],
                }
                operations.append(operation)

            conn.close()
            return operations

        except Exception as e:
            logger.error(f"Failed to get sync operations: {e}")
            return []
