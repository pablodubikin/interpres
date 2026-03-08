"""Manages Discord thread creation."""
import discord


class ThreadManager:
    """Manages Discord thread creation."""
    
    @staticmethod
    async def get_or_create_thread(message, thread_name: str) -> discord.Thread:
        """Get existing thread or create a new one."""
        if isinstance(message.channel, discord.Thread):
            return message.channel
        return await message.create_thread(
            name=thread_name,
            auto_archive_duration=60
        )

