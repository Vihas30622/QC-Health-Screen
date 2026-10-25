"""
core/session_store.py
======================
Minimal in-memory session store.

Per the spec's data-handling requirements (Section 17):
  - Sensitive health information is minimized
  - Data is not permanently stored unless necessary
  - Sessions are isolated from one another
  - No unnecessary personal identification is collected

For an academic prototype this means: no database, no disk persistence,
no names/emails/anything identifying — just a random session id mapping to
the in-progress screening state, held in process memory, expiring after a
period of inactivity.

This is intentionally swappable: replace this module with a Redis-backed
store for a multi-worker deployment without touching the API layer.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, Optional

SESSION_TTL_SECONDS = 30 * 60  # 30 minutes of inactivity


@dataclass
class SessionState:
    session_id: str
    created_at: float = field(default_factory=time.time)
    last_touched_at: float = field(default_factory=time.time)
    basic_profile: Optional[Dict[str, Any]] = None
    initial_screening: Optional[Dict[str, Any]] = None
    followup_answers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    disease_predictions: Dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.last_touched_at = time.time()


class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, SessionState] = {}
        self._lock = Lock()

    def create(self) -> SessionState:
        session_id = uuid.uuid4().hex
        state = SessionState(session_id=session_id)
        with self._lock:
            self._sessions[session_id] = state
        return state

    def get(self, session_id: str) -> Optional[SessionState]:
        self._evict_expired()
        with self._lock:
            state = self._sessions.get(session_id)
            if state is not None:
                state.touch()
            return state

    def _evict_expired(self) -> None:
        now = time.time()
        with self._lock:
            expired = [
                sid
                for sid, s in self._sessions.items()
                if now - s.last_touched_at > SESSION_TTL_SECONDS
            ]
            for sid in expired:
                del self._sessions[sid]


# Process-wide singleton. For a multi-worker deployment, swap this for a
# shared store (Redis, etc.) — see module docstring.
session_store = SessionStore()
