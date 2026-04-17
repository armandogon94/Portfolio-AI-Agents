"""Agent state bus for live event streaming.

See DECISIONS.md DEC-16 (SSE transport) and DEC-27 (in-process asyncio pub/sub).

The bus has one producer (the crew background thread) and one-or-more asyncio
subscribers (the SSE endpoint, the Chainlit UI). Publishers may be called from
any thread; subscribers must run in an event loop.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from src.models.schemas import AgentStateEvent

logger = logging.getLogger(__name__)

_TERMINAL_STATES = {"completed", "failed"}


@dataclass
class _TaskChannel:
    buffer: deque
    subscribers: list[asyncio.Queue] = field(default_factory=list)
    terminal: bool = False
    last_activity: float = field(default_factory=time.time)


class AgentStateBus:
    """In-process asyncio pub/sub for agent state events."""

    def __init__(self, ttl_seconds: int = 300, buffer_size: int = 1000):
        self._channels: dict[str, _TaskChannel] = {}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds
        self._buffer_size = buffer_size
        self._loop: asyncio.AbstractEventLoop | None = None
        # Slice-27: optional persistence side-channel so the share page
        # can replay the timeline after the in-memory buffer is gone.
        self._persister = None  # type: ignore[assignment]

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Bind the running event loop so cross-thread publishes can dispatch."""
        self._loop = loop

    def bind_persister(self, save_event) -> None:
        """Attach a persistence callback ``save_event(task_id, event)`` (slice-27).

        Called best-effort on every publish — failures are logged but do
        not block live delivery to subscribers.
        """
        self._persister = save_event

    def publish(self, task_id: str, event: AgentStateEvent) -> None:
        """Publish an event. Thread-safe; can be called from any thread."""
        with self._lock:
            channel = self._channels.get(task_id)
            if channel is None:
                channel = _TaskChannel(buffer=deque(maxlen=self._buffer_size))
                self._channels[task_id] = channel
            channel.buffer.append(event)
            channel.last_activity = time.time()
            if event.state in _TERMINAL_STATES:
                channel.terminal = True
            subscribers = list(channel.subscribers)

        for queue in subscribers:
            self._deliver(queue, event)

        # Slice-27: best-effort persistence so the share page can replay
        # the full timeline after a restart. Never blocks live delivery.
        if self._persister is not None:
            try:
                self._persister(task_id, event)
            except Exception:  # pragma: no cover — telemetry must not kill the crew
                logger.exception("Failed to persist agent_state event")

    def _deliver(self, queue: asyncio.Queue, event: AgentStateEvent) -> None:
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._put_or_drop, queue, event)
        else:
            self._put_or_drop(queue, event)

    @staticmethod
    def _put_or_drop(queue: asyncio.Queue, event: AgentStateEvent) -> None:
        """Put event on queue; if full, drop the oldest entry and log a WARN."""
        try:
            queue.put_nowait(event)
            return
        except asyncio.QueueFull:
            pass

        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:  # pragma: no cover — race from concurrent producers
            pass
        logger.warning("Dropped oldest event in agent state queue (slow subscriber)")

    async def subscribe(self, task_id: str) -> AsyncIterator[AgentStateEvent]:
        """Yield events for a task. Replays buffered events before live ones.

        Ends when a terminal event (completed/failed) has been yielded.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=self._buffer_size)

        with self._lock:
            channel = self._channels.get(task_id)
            if channel is None:
                channel = _TaskChannel(buffer=deque(maxlen=self._buffer_size))
                self._channels[task_id] = channel
            channel.subscribers.append(queue)
            replay = list(channel.buffer)
            channel.last_activity = time.time()

        try:
            for event in replay:
                yield event
                if event.state in _TERMINAL_STATES:
                    return

            while True:
                event = await queue.get()
                yield event
                if event.state in _TERMINAL_STATES:
                    return
        finally:
            with self._lock:
                ch = self._channels.get(task_id)
                if ch is not None and queue in ch.subscribers:
                    ch.subscribers.remove(queue)

    def has_channel(self, task_id: str) -> bool:
        with self._lock:
            return task_id in self._channels

    def cleanup(self) -> int:
        """Delete terminal channels with no active subscribers past TTL."""
        now = time.time()
        with self._lock:
            expired = [
                tid
                for tid, ch in self._channels.items()
                if ch.terminal and not ch.subscribers and now - ch.last_activity > self._ttl
            ]
            for tid in expired:
                del self._channels[tid]
            return len(expired)


_bus: AgentStateBus | None = None


def get_state_bus() -> AgentStateBus:
    """Process-wide AgentStateBus singleton (DEC-27)."""
    global _bus
    if _bus is None:
        _bus = AgentStateBus()
    return _bus
