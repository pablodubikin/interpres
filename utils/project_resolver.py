"""Resolves project paths from Discord channel topics."""
import os
from typing import Optional
import discord
from config import Config


class ProjectResolver:
    """Resolves project paths from Discord channel topics."""
    
    @staticmethod
    def get_project_path(channel) -> Optional[str]:
        """Extract project relative path from channel topic."""
        if isinstance(channel, discord.Thread):
            parent_channel = channel.parent
            return parent_channel.topic if parent_channel else None
        return channel.topic
    
    @staticmethod
    def get_full_project_path(channel) -> Optional[str]:
        """Get full absolute path to project directory, guarded against path traversal."""
        relative_path = ProjectResolver.get_project_path(channel)
        if not relative_path:
            return None
        resolved = os.path.realpath(os.path.join(Config.BASE_DIR, relative_path))
        base_real = os.path.realpath(Config.BASE_DIR)
        if not resolved.startswith(base_real + os.sep) and resolved != base_real:
            return None
        return resolved

