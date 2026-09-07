import json
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from leggen.repositories.db import get_db_connection


class SessionRepository:
    """Repository for EnableBanking session storage."""

    def persist(self, session_data: dict[str, Any]) -> str:
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
                    session_data.get("created_at", datetime.now(UTC).isoformat()),
                    session_data.get("status", "active"),
                ),
            )
            conn.commit()

        logger.info(f"Persisted session {session_id}")
        return session_id

    def get_sessions(self) -> list[dict[str, Any]]:
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

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get a single session by id, or None if it isn't stored."""
        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()

        if row is None:
            return None

        session = dict(row)
        if session.get("accounts"):
            session["accounts"] = json.loads(session["accounts"])
        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if a row was deleted."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            deleted = cursor.rowcount > 0
            cursor.execute(
                "DELETE FROM expiry_notifications WHERE session_id = ?", (session_id,)
            )
            conn.commit()
            return deleted

    def was_expiry_notified(self, session_id: str, threshold: int) -> bool:
        """Check whether an expiry notification was already sent for this
        session at the given threshold (days left; 0 means expired)."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM expiry_notifications WHERE session_id = ? AND threshold = ?",
                (session_id, threshold),
            )
            return cursor.fetchone() is not None

    def mark_expiry_notified(self, session_id: str, threshold: int) -> None:
        """Record that an expiry notification was sent for this session/threshold."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO expiry_notifications (session_id, threshold, sent_at)
                   VALUES (?, ?, ?)""",
                (session_id, threshold, datetime.now(UTC).isoformat()),
            )
            conn.commit()
