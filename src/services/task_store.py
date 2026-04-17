"""In-memory task store for async crew execution.

See DECISIONS.md DEC-02 for rationale (BackgroundTasks, not Celery).
"""

import time
import uuid
import threading


class TaskStore:
    def __init__(self, ttl_seconds: int = 3600, voice_session_store=None):
        """Parameters
        ----------
        ttl_seconds:
            In-memory retention window.
        voice_session_store:
            Optional :class:`VoiceSessionStore`. When provided, `cleanup()`
            cascades the eviction so abandoned voice sessions don't leak
            (Phase-4 review item I1).
        """
        self._tasks: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds
        self._voice_sessions = voice_session_store

    def create(self, topic: str, domain: str | None, webhook_url: str | None = None) -> str:
        task_id = str(uuid.uuid4())
        with self._lock:
            self._tasks[task_id] = {
                "task_id": task_id,
                "topic": topic,
                "domain": domain,
                "status": "pending",
                "result": None,
                "created_at": time.time(),
                "webhook_url": webhook_url,
            }
        # Lazily evict expired tasks so memory doesn't grow unboundedly (I1)
        self.cleanup()
        return task_id

    def get(self, task_id: str) -> dict | None:
        with self._lock:
            task = self._tasks.get(task_id)
            # Return a shallow copy so callers can't mutate stored state (I2)
            return dict(task) if task is not None else None

    def update(self, task_id: str, status: str, result: str | None = None) -> None:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = status
                self._tasks[task_id]["result"] = result

    def active_count(self) -> int:
        """Number of tasks currently in pending or running state."""
        with self._lock:
            return sum(1 for t in self._tasks.values() if t["status"] in ("pending", "running"))

    def cleanup(self) -> int:
        """Remove expired tasks. Cascades to the VoiceSessionStore when wired.

        Returns the number of tasks removed.
        """
        now = time.time()
        with self._lock:
            expired = [
                tid for tid, t in self._tasks.items()
                if now - t["created_at"] > self._ttl
            ]
            for tid in expired:
                del self._tasks[tid]
        if self._voice_sessions is not None:
            for tid in expired:
                try:
                    self._voice_sessions.clear(tid)
                except Exception:  # pragma: no cover — cleanup must not raise
                    pass
        return len(expired)
