"""Manages Cursor session persistence."""
import asyncio
import os
import json
from typing import Dict, Optional
from config import Config, logger


class SessionManager:
    """Manages Cursor session persistence."""

    def __init__(self):
        self.sessions: Dict[int, str] = {}
        self._lock = asyncio.Lock()
        self.load_sessions()
    
    def load_sessions(self):
        """Load session IDs from JSON file."""
        if os.path.exists(Config.SESSIONS_FILE):
            try:
                with open(Config.SESSIONS_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert string keys to int (Discord thread IDs are integers)
                    self.sessions = {int(k): v for k, v in data.items()}
            except (json.JSONDecodeError, ValueError, IOError) as e:
                logger.warning(f"Failed to load sessions: {e}")
                print(f"⚠️ Failed to load sessions: {e}")
                self.sessions = {}
    
    def save_sessions(self):
        """Save session IDs to JSON file."""
        try:
            with open(Config.SESSIONS_FILE, 'w') as f:
                # Convert int keys to strings for JSON compatibility
                data = {str(k): v for k, v in self.sessions.items()}
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save sessions: {e}")
            print(f"⚠️ Failed to save sessions: {e}")
    
    def get_session(self, thread_id: int) -> Optional[str]:
        """Get session ID for a thread."""
        return self.sessions.get(thread_id)
    
    async def set_session(self, thread_id: int, session_id: Optional[str]):
        """Set session ID for a thread and save."""
        async with self._lock:
            if session_id:
                self.sessions[thread_id] = session_id
            elif thread_id in self.sessions:
                del self.sessions[thread_id]
            self.save_sessions()

