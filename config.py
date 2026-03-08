"""Configuration settings for the Discord bot."""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler


class Config:
    """Configuration settings for the bot."""
    BASE_DIR = os.getenv("PROJECTS_BASE_DIR", os.path.expanduser("~/projects"))
    SESSIONS_FILE = "sessions.json"  # File to persist session IDs
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

