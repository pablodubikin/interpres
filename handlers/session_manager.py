"""Manages Claude session persistence."""
import asyncio
import os
import json
from typing import Dict, Optional, Tuple
from config import Config, logger


class SessionManager:
    """Manages Claude session persistence."""

    def __init__(self):
        # {thread_id: {"session_id": str, "cwd": str}}
        self.sessions: Dict[int, dict] = {}
        self._lock = asyncio.Lock()
        self.load_sessions()

    def load_sessions(self):
        """Load sessions from JSON file, handling legacy string-only entries."""
        if not os.path.exists(Config.SESSIONS_FILE):
            return
        try:
            with open(Config.SESSIONS_FILE, 'r') as f:
                data = json.load(f)
            self.sessions = {}
            for k, v in data.items():
                thread_id = int(k)
                if isinstance(v, dict):
                    self.sessions[thread_id] = v
                else:
                    # Legacy format: bare session_id string, cwd unknown
                    self.sessions[thread_id] = {"session_id": v, "cwd": None}
        except (json.JSONDecodeError, ValueError, IOError) as e:
            logger.warning(f"Failed to load sessions: {e}")
            self.sessions = {}

    def save_sessions(self):
        """Save sessions to JSON file."""
        try:
            with open(Config.SESSIONS_FILE, 'w') as f:
                json.dump({str(k): v for k, v in self.sessions.items()}, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save sessions: {e}")

    def get_session(self, thread_id: int) -> Tuple[Optional[str], Optional[str]]:
        """Return (session_id, cwd) for a thread, or (None, None) if not found."""
        entry = self.sessions.get(thread_id)
        if not entry:
            return None, None
        return entry.get("session_id"), entry.get("cwd")

    async def set_session(self, thread_id: int, session_id: Optional[str], cwd: Optional[str] = None):
        """Persist session_id and the cwd it was created under."""
        async with self._lock:
            if session_id:
                self.sessions[thread_id] = {"session_id": session_id, "cwd": cwd}
            elif thread_id in self.sessions:
                del self.sessions[thread_id]
            self.save_sessions()
