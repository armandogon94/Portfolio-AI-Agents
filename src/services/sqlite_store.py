"""SQLite-backed result store for completed crew runs.

See DECISIONS.md DEC-14 for rationale (SQLite for history, not replacing TaskStore).
"""

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS crew_results (
    task_id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    domain TEXT,
    result TEXT NOT NULL,
    duration_seconds REAL,
    created_at TEXT NOT NULL
);
"""


class SQLiteResultStore:
    """Persists completed crew run results to a SQLite database."""

    def __init__(self, db_path: str = "data/results.db"):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)
            conn.commit()
        logger.debug(f"SQLite result store ready at {self._db_path}")

    def save(
        self,
        task_id: str,
        topic: str,
        domain: str | None,
        result: str,
        duration_seconds: float = 0.0,
    ) -> None:
        """Persist a completed task result."""
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO crew_results
                    (task_id, topic, domain, result, duration_seconds, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (task_id, topic, domain, result, duration_seconds, created_at),
            )
            conn.commit()
        logger.debug(f"Saved result for task {task_id}")

    def get(self, task_id: str) -> dict | None:
        """Retrieve a persisted result by task_id. Returns None if not found."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM crew_results WHERE task_id = ?", (task_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def list_recent(self, limit: int = 20) -> list[dict]:
        """Return most recent N completed runs, newest first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM crew_results ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
