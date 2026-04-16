"""Unit tests for AgentStateBus (slice-19).

Covers:
- publish→subscribe replay (late subscribers still receive all prior events)
- multi-subscriber delivery to the same task_id
- task_id isolation
- bounded queue with drop-oldest-with-warning
- TTL cleanup of terminal channels
"""

import asyncio
import time

import pytest


def _make_event(
    task_id: str = "t1",
    state: str = "active",
    agent_role: str = "researcher",
    detail: str = "",
):
    """Construct an AgentStateEvent for tests."""
    from src.models.schemas import AgentStateEvent

    return AgentStateEvent(
        task_id=task_id,
        agent_role=agent_role,
        state=state,
        detail=detail,
        ts="2026-04-16T10:00:00+00:00",
    )


@pytest.mark.unit
class TestAgentStateBusPublishSubscribe:
    async def test_subscribe_after_publish_replays_buffered_events(self):
        """A subscriber that joins after publish still receives all cached events."""
        from src.services.state_bus import AgentStateBus

        bus = AgentStateBus(ttl_seconds=60, buffer_size=100)

        bus.publish("t1", _make_event(state="queued"))
        bus.publish("t1", _make_event(state="active"))
        bus.publish("t1", _make_event(state="completed"))  # terminal

        received = []
        async for ev in bus.subscribe("t1"):
            received.append(ev.state)

        assert received == ["queued", "active", "completed"]

    async def test_multiple_subscribers_same_task_both_receive_all_events(self):
        """Two concurrent subscribers on one task each receive the full event sequence."""
        from src.services.state_bus import AgentStateBus

        bus = AgentStateBus(ttl_seconds=60, buffer_size=100)

        async def consume():
            out: list[str] = []
            async for ev in bus.subscribe("t1"):
                out.append(ev.state)
            return out

        a = asyncio.create_task(consume())
        b = asyncio.create_task(consume())

        # Let both tasks register their queues before publishing.
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        bus.publish("t1", _make_event(state="queued"))
        bus.publish("t1", _make_event(state="active"))
        bus.publish("t1", _make_event(state="completed"))

        a_events = await asyncio.wait_for(a, timeout=1.0)
        b_events = await asyncio.wait_for(b, timeout=1.0)

        assert a_events == ["queued", "active", "completed"]
        assert b_events == ["queued", "active", "completed"]

    async def test_different_task_ids_are_isolated(self):
        """Publishing to task A does not deliver events to subscribers of task B."""
        from src.services.state_bus import AgentStateBus

        bus = AgentStateBus(ttl_seconds=60, buffer_size=100)

        bus.publish("t1", _make_event(task_id="t1", state="queued"))
        bus.publish("t1", _make_event(task_id="t1", state="completed"))
        bus.publish("t2", _make_event(task_id="t2", state="queued"))
        bus.publish("t2", _make_event(task_id="t2", state="completed"))

        t1 = [ev async for ev in bus.subscribe("t1")]
        t2 = [ev async for ev in bus.subscribe("t2")]

        assert len(t1) == 2
        assert len(t2) == 2
        assert {e.task_id for e in t1} == {"t1"}
        assert {e.task_id for e in t2} == {"t2"}

    async def test_queue_full_drops_oldest_and_logs_warning(self, caplog):
        """When a subscriber's queue fills, the bus drops the oldest event and logs a WARN."""
        from src.services.state_bus import AgentStateBus

        queue: asyncio.Queue = asyncio.Queue(maxsize=2)

        with caplog.at_level("WARNING", logger="src.services.state_bus"):
            AgentStateBus._put_or_drop(queue, _make_event(detail="a"))
            AgentStateBus._put_or_drop(queue, _make_event(detail="b"))
            AgentStateBus._put_or_drop(queue, _make_event(detail="c"))  # should drop "a"

        assert queue.qsize() == 2
        first = queue.get_nowait()
        second = queue.get_nowait()
        assert first.detail == "b"
        assert second.detail == "c"
        assert any(
            "Dropped oldest" in rec.message
            for rec in caplog.records
            if rec.levelname == "WARNING"
        )

    def test_cleanup_removes_terminal_channels_after_ttl(self):
        """cleanup() deletes channels that are terminal, unsubscribed, and past TTL."""
        from src.services.state_bus import AgentStateBus

        bus = AgentStateBus(ttl_seconds=0, buffer_size=10)
        bus.publish("t1", _make_event(state="completed"))
        bus.publish("t2", _make_event(state="active"))  # non-terminal

        assert bus.has_channel("t1")
        assert bus.has_channel("t2")

        time.sleep(0.01)
        removed = bus.cleanup()

        assert removed == 1
        assert not bus.has_channel("t1")
        assert bus.has_channel("t2")  # still active, not cleaned
