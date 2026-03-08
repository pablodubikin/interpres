"""Main Discord bot entry point."""
import os
import discord
from config import Config, logger
from handlers import SessionManager, ClaudeAgent, MetabotHandler
from utils import ProjectResolver, ThreadManager, MessageFormatter

ATTACHMENT_DIR = "/tmp/claude_attachments"


class DiscordBot:
    """Main Discord bot class."""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.claude_agent = ClaudeAgent(self.session_manager)
        self.metabot_handler = MetabotHandler()
        
        self.token = os.getenv("DISCORD_TOKEN")
        if not self.token:
            raise ValueError("DISCORD_TOKEN environment variable not set")
        
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        
        self.client = discord.Client(intents=intents)
        self._setup_events()
    
    def _setup_events(self):
        """Set up Discord event handlers."""
        @self.client.event
        async def on_ready():
            logger.info(f"Bot started - logged in as {self.client.user}")
        
        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return
            
            if not message.content.strip() and not message.attachments:
                return
            
            if message.content.startswith("/metabot "):
                command = message.content[len("/metabot "):].strip()
                logger.info(f"Metabot command from {message.author}: {command}")
                await self.metabot_handler.handle_command(self.client, message, command)
                return
            
            if message.content.strip() == "/projects":
                logger.info(f"Projects list requested by {message.author}")
                await self._handle_list_projects(message)
                return
            
            if message.content.startswith("/channel "):
                project_name = message.content[len("/channel "):].strip()
                logger.info(f"Channel creation requested by {message.author} for project: {project_name}")
                await self._handle_create_channel(message, project_name)
                return
            
            logger.info(f"Prompt from {message.author} in #{message.channel}: {message.content[:100]}")
            await self._handle_prompt(message)
    
    def _get_project_dirs(self):
        """Return sorted list of non-hidden directory names in BASE_DIR."""
        return sorted(
            entry for entry in os.listdir(Config.BASE_DIR)
            if os.path.isdir(os.path.join(Config.BASE_DIR, entry))
            and not entry.startswith(".")
        )
    
    async def _handle_list_projects(self, message: discord.Message):
        """List all available projects."""
        projects = self._get_project_dirs()
        if not projects:
            await message.channel.send("No projects found.")
            return
        listing = "\n".join(f"• `{p}`" for p in projects)
        await message.channel.send(
            f"📁 **Available projects** ({len(projects)}):\n{listing}\n\n"
            f"Use `/channel <name>` to create a channel for one."
        )
    
    async def _handle_create_channel(self, message: discord.Message, project_name: str):
        """Create a project channel on demand."""
        project_path = os.path.realpath(os.path.join(Config.BASE_DIR, project_name))
        base_real = os.path.realpath(Config.BASE_DIR)
        if not project_path.startswith(base_real + os.sep) and project_path != base_real:
            await message.channel.send("⚠️ Invalid project name.")
            return
        if not os.path.isdir(project_path):
            await message.channel.send(f"⚠️ No project directory found at `{project_path}`")
            return
        
        guild = message.guild
        if not guild:
            return
        
        existing = discord.utils.get(guild.text_channels, topic=project_name)
        if existing:
            await message.channel.send(f"Channel already exists: {existing.mention}")
            return
        
        channel_name = project_name.lower().replace("_", "-").replace(" ", "-")
        new_channel = await guild.create_text_channel(channel_name, topic=project_name)
        await message.channel.send(f"✅ Created {new_channel.mention} for `{project_name}`")
    
    async def _handle_prompt(self, message: discord.Message):
        """Handle regular prompt messages."""
        prompt = message.content.strip()

        project_root = ProjectResolver.get_full_project_path(message.channel)
        if not project_root:
            # Use the base projects directory as default for general channel
            project_root = Config.BASE_DIR

        saved_paths = []
        if message.attachments:
            os.makedirs(ATTACHMENT_DIR, exist_ok=True)
            for att in message.attachments:
                safe_name = os.path.basename(att.filename)
                dest = os.path.join(ATTACHMENT_DIR, safe_name)
                await att.save(dest)
                saved_paths.append(dest)
                logger.info(f"Saved attachment: {dest}")
            attachment_note = "\n\nThe user has attached the following file(s):\n" + "\n".join(f"- {p}" for p in saved_paths)
            prompt = (prompt or "(no text provided)") + attachment_note

        thread_title = message.content.strip()[:30] or message.attachments[0].filename[:30] if message.attachments else "prompt"
        thread = await ThreadManager.get_or_create_thread(message, f"Claude: {thread_title}")
        await thread.send("💡 Got it – running Claude...")

        _, output_text = await self.claude_agent.execute(
            prompt, project_root, thread.id
        )

        if not output_text:
            output_text = "No response received."
        
        await MessageFormatter.send_formatted(thread, output_text)
    
    def run(self):
        """Run the bot."""
        self.client.run(self.token)


# --- ENTRY POINT ---
if __name__ == "__main__":
    bot = DiscordBot()
    bot.run()
