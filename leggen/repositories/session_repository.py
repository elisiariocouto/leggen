import json
from datetime import datetime
from typing import Any, Dict, List

from loguru import logger

from leggen.repositories.db import get_db_connection


class SessionRepository:
    """Repository for EnableBanking session storage."""

    def create_table(self):
        """Create the sessions table if it doesn't exist."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    aspsp_name TEXT NOT NULL,
                    aspsp_country TEXT NOT NULL,
                    accounts JSON,
                    valid_until DATETIME,
                    created_at DATETIME,
                    status TEXT DEFAULT 'active'
                )
            """)
            conn.commit()

    def persist(self, session_data: Dict[str, Any]) -> str:
        """Store a session in the database. Returns the session_id."""
        session_id = session_data["session_id"]
        accounts = session_data.get("accounts")
        accounts_json = json.dumps(accounts) if accounts is not None else None

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO sessions
                    (session_id, aspsp_name, aspsp_country, accounts, valid_until, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    session_data["aspsp_name"],
                    session_data["aspsp_country"],
                    accounts_json,
                    session_data.get("valid_until"),
                    session_data.get("created_at", datetime.now().isoformat()),
                    session_data.get("status", "active"),
                ),
            )
            conn.commit()

        logger.info(f"Persisted session {session_id}")
        return session_id

    def get_sessions(self) -> List[Dict[str, Any]]:
        """Get all sessions."""
        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC")
            rows = cursor.fetchall()

        sessions = []
        for row in rows:
            session = dict(row)
            if session.get("accounts"):
                session["accounts"] = json.loads(session["accounts"])
            sessions.append(session)

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if a row was deleted."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0
