"""Clean up all project channels and categories created by this bot."""
import os
import discord
from config import Config, logger

GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))
CATEGORY_PREFIX = os.getenv("DISCORD_CATEGORY", "projects")


async def cleanup(client: discord.Client):
    guild = client.get_guild(GUILD_ID)
    if not guild:
        logger.error(f"Guild {GUILD_ID} not found. Set DISCORD_GUILD_ID env var.")
        return

    deleted = 0
    for category in guild.categories:
        if not (category.name == CATEGORY_PREFIX or category.name.startswith(f"{CATEGORY_PREFIX}-")):
            continue

        for channel in category.text_channels:
            await channel.delete()
            logger.info(f"Deleted #{channel.name}")
            deleted += 1

        await category.delete()
        logger.info(f"Deleted category: {category.name}")

    logger.info(f"Cleanup complete. Deleted {deleted} channels.")


def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN environment variable not set")
    if not GUILD_ID:
        raise ValueError("DISCORD_GUILD_ID environment variable not set")

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        logger.info(f"Connected as {client.user}, cleaning up channels...")
        try:
            await cleanup(client)
        finally:
            await client.close()

    client.run(token)


if __name__ == "__main__":
    main()
