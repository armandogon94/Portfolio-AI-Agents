"""Per-task voice conversation state (slice-26).

A light state machine the TwiML webhook uses to decide what to say
next and whether to hang up. Conversation state stays in-memory
keyed by task_id — matches the TaskStore's lifetime semantics.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field


@dataclass
class VoiceTurn:
    prompt: str
    heard: str = ""


@dataclass
class VoiceSession:
    task_id: str
    max_turns: int = 6
    turns: list[VoiceTurn] = field(default_factory=list)

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    @property
    def is_complete(self) -> bool:
        return self.turn_count >= self.max_turns

    def record_turn(self, prompt: str, heard: str = "") -> None:
        self.turns.append(VoiceTurn(prompt=prompt, heard=heard))

    def transcript(self) -> str:
        lines = []
        for i, t in enumerate(self.turns, 1):
            lines.append(f"Turn {i} agent: {t.prompt}")
            if t.heard:
                lines.append(f"Turn {i} caller: {t.heard}")
        return "\n".join(lines)


class VoiceSessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, VoiceSession] = {}
        self._lock = threading.Lock()

    def get_or_create(self, task_id: str, max_turns: int = 6) -> VoiceSession:
        with self._lock:
            session = self._sessions.get(task_id)
            if session is None:
                session = VoiceSession(task_id=task_id, max_turns=max_turns)
                self._sessions[task_id] = session
            return session

    def get(self, task_id: str) -> VoiceSession | None:
        with self._lock:
            return self._sessions.get(task_id)

    def clear(self, task_id: str) -> None:
        with self._lock:
            self._sessions.pop(task_id, None)


_store: VoiceSessionStore | None = None


def get_voice_session_store() -> VoiceSessionStore:
    global _store
    if _store is None:
        _store = VoiceSessionStore()
    return _store
