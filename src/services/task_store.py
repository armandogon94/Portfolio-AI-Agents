"""In-memory task store for async crew execution.

See DECISIONS.md DEC-02 for rationale (BackgroundTasks, not Celery).
"""

import time
import uuid
import threading


class TaskStore:
    def __init__(self, ttl_seconds: int = 3600):
        self._tasks: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds

    def create(self, topic: str, domain: str | None) -> str:
        task_id = str(uuid.uuid4())
        with self._lock:
            self._tasks[task_id] = {
                "task_id": task_id,
                "topic": topic,
                "domain": domain,
                "status": "pending",
                "result": None,
                "created_at": time.time(),
            }
        return task_id

    def get(self, task_id: str) -> dict | None:
        with self._lock:
            return self._tasks.get(task_id)

    def update(self, task_id: str, status: str, result: str | None = None) -> None:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = status
                self._tasks[task_id]["result"] = result

    def cleanup(self) -> int:
        """Remove expired tasks. Returns number removed."""
        now = time.time()
        removed = 0
        with self._lock:
            expired = [
                tid for tid, t in self._tasks.items()
                if now - t["created_at"] > self._ttl
            ]
            for tid in expired:
                del self._tasks[tid]
                removed += 1
        return removed
