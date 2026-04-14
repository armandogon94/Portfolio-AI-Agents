import time
import uuid

import pytest


@pytest.mark.unit
class TestTaskStore:
    """In-memory task store tests. See DECISIONS.md DEC-02."""

    def test_create_returns_task_id(self):
        """create() returns a valid UUID string."""
        from src.services.task_store import TaskStore

        store = TaskStore()
        task_id = store.create(topic="test", domain=None)
        uuid.UUID(task_id, version=4)  # raises if invalid

    def test_get_returns_task(self):
        """get() returns task dict with status, topic, result fields."""
        from src.services.task_store import TaskStore

        store = TaskStore()
        task_id = store.create(topic="test", domain="healthcare")
        task = store.get(task_id)
        assert task is not None
        assert task["status"] == "pending"
        assert task["topic"] == "test"
        assert task["domain"] == "healthcare"
        assert task["result"] is None

    def test_update_changes_status(self):
        """update() transitions status and sets result."""
        from src.services.task_store import TaskStore

        store = TaskStore()
        task_id = store.create(topic="test", domain=None)
        store.update(task_id, status="completed", result="done")
        task = store.get(task_id)
        assert task["status"] == "completed"
        assert task["result"] == "done"

    def test_get_nonexistent_returns_none(self):
        """get() returns None for unknown task ID."""
        from src.services.task_store import TaskStore

        store = TaskStore()
        assert store.get("nonexistent-id") is None

    def test_cleanup_removes_expired(self):
        """cleanup() removes tasks older than TTL."""
        from src.services.task_store import TaskStore

        store = TaskStore(ttl_seconds=0)  # expire immediately
        task_id = store.create(topic="test", domain=None)
        time.sleep(0.01)
        store.cleanup()
        assert store.get(task_id) is None

    def test_cleanup_triggered_automatically_on_create(self):
        """Expired tasks are cleaned up automatically when new tasks are created."""
        from src.services.task_store import TaskStore

        store = TaskStore(ttl_seconds=0)  # expire immediately
        old_id = store.create(topic="old", domain=None)
        time.sleep(0.01)
        # Creating a new task should trigger cleanup of the expired one
        store.create(topic="new", domain=None)
        assert store.get(old_id) is None

    def test_get_returns_copy_not_reference(self):
        """get() returns a copy so mutations don't affect stored state."""
        from src.services.task_store import TaskStore

        store = TaskStore()
        task_id = store.create(topic="test", domain=None)
        task = store.get(task_id)
        # Mutate the returned dict
        task["status"] = "hacked"
        task["result"] = "tampered"
        # The stored task must be unaffected
        stored = store.get(task_id)
        assert stored["status"] == "pending"
        assert stored["result"] is None
