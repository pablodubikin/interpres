"""Configuration settings for the Discord bot."""
import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler


class Config:
    """Configuration settings for the bot."""
    BASE_DIR = os.getenv("PROJECTS_BASE_DIR", os.path.expanduser("~/projects"))
    SESSIONS_FILE = "sessions.json"  # File to persist session IDs

    # Per-guild access control. Loaded from the GUILD_BASE_DIRS env var (JSON).
    # Each key is a guild ID (string). Each value is either:
    #   - a string: the base directory for that guild (no channel restriction)
    #   - a dict:   {"base_dir": "...", "channel_id": 123}  (channel_id is optional)
    # Guilds not present in this map are silently ignored.
    # Example env var value:
    #   GUILD_BASE_DIRS='{"111": "/home/user/projects", "222": {"base_dir": "/home/user/projects/foo", "channel_id": 333}}'
    GUILD_BASE_DIRS: dict = json.loads(os.getenv("GUILD_BASE_DIRS", "{}"))

    @classmethod
    def get_guild_base_dir(cls, guild_id: int) -> str | None:
        """Return the base directory allowed for a guild, or None if not configured."""
        entry = cls.GUILD_BASE_DIRS.get(str(guild_id))
        if entry is None:
            return None
        if isinstance(entry, str):
            return entry
        return entry.get("base_dir")

    @classmethod
    def get_guild_channel_id(cls, guild_id: int) -> int | None:
        """Return the allowed channel ID for a guild, or None if unrestricted."""
        entry = cls.GUILD_BASE_DIRS.get(str(guild_id))
        if not isinstance(entry, dict):
            return None
        channel_id = entry.get("channel_id")
        return int(channel_id) if channel_id is not None else None
    STARTUP_ANNOUNCE_CHANNEL_ID: int | None = int(os.getenv("STARTUP_ANNOUNCE_CHANNEL_ID")) if os.getenv("STARTUP_ANNOUNCE_CHANNEL_ID") else None
    LOG_FILE = "bot.log"  # File to write bot logs
    PID_FILE = "bot.pid"  # File to store bot process ID
    DISCORD_MAX_MESSAGE_LENGTH = 1900  # Discord message limit with buffer
    CODE_BLOCK_PREFIXES = ('def ', 'class ', 'import ', 'from ', 'const ', 'let ', 'var ', 'function ', '#')


# Initialize logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(Config.LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

