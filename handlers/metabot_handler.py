"""Handles metabot commands."""
import os
import subprocess
import sys
from typing import Optional
import discord
import psutil
from config import Config, logger
from utils import MessageFormatter


class MetabotHandler:
    """Handles metabot commands."""
    
    @staticmethod
    def read_pid() -> Optional[int]:
        """Read process ID from PID file."""
        if not os.path.exists(Config.PID_FILE):
            return None
        try:
            with open(Config.PID_FILE, 'r') as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return None
    
    @staticmethod
    def is_process_running(pid: int) -> bool:
        """Check if process with given PID is running."""
        try:
            return psutil.pid_exists(pid)
        except Exception:
            return False
    
    async def handle_status(self, channel):
        """Handle metabot status command."""
        pid = self.read_pid()
        if pid is None:
            await channel.send("⚠️ Could not read PID file. Bot may not be properly initialized.")
            return
        
        if self.is_process_running(pid):
            await channel.send(f"✅ **Bot Status: RUNNING**\n📋 PID: `{pid}`")
        else:
            await channel.send(f"❌ **Bot Status: STOPPED**\n📋 PID file exists (`{pid}`) but process is not running.")
    
    async def handle_logs(self, channel):
        """Handle metabot logs command."""
        try:
            if not os.path.exists(Config.LOG_FILE):
                await channel.send("⚠️ Log file does not exist yet.")
                return
            
            with open(Config.LOG_FILE, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-50:] if len(lines) > 50 else lines
                log_content = ''.join(recent_lines)
            
            if not log_content.strip():
                await channel.send("📋 Log file is empty.")
                return
            
            escaped_content = MessageFormatter.escape_backticks(log_content)
            chunks = MessageFormatter.chunk_message(escaped_content)
            
            if len(chunks) == 1:
                await channel.send(f"📋 **Recent Logs** (last 50 lines):\n```\n{escaped_content}\n```")
            else:
                await channel.send(f"📋 **Recent Logs** (last 50 lines, split into {len(chunks)} parts):")
                for i, chunk in enumerate(chunks, 1):
                    await channel.send(f"```\nPart {i}/{len(chunks)}:\n{chunk}\n```")
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            await channel.send(f"❌ Error reading logs: {str(e)}")
    
    async def handle_restart(self, client: discord.Client, channel):
        """Handle metabot restart command."""
        logger.warning("Restart command received - initiating restart...")
        await channel.send("🔄 Restarting bot...")
        
        try:
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot.py'))
            python_executable = sys.executable
            cwd = os.path.dirname(script_path)

            # Spawn a detached process that waits 2s then starts the bot.
            # Avoids shell=True to prevent injection via cwd or path values.
            delay_cmd = (
                "import time, subprocess, sys; "
                "time.sleep(2); "
                "subprocess.Popen([sys.argv[1], sys.argv[2]])"
            )

            if os.name == 'nt':  # Windows
                subprocess.Popen(
                    [python_executable, "-c", delay_cmd, python_executable, script_path],
                    cwd=cwd,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                )
            else:  # Unix-like
                subprocess.Popen(
                    [python_executable, "-c", delay_cmd, python_executable, script_path],
                    cwd=cwd,
                    start_new_session=True,
                )
            
            logger.info("New bot process spawned, exiting current process...")
            await client.close()
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error during restart: {e}")
            await channel.send(f"❌ Error restarting bot: {str(e)}")
    
    async def handle_command(self, client: discord.Client, message: discord.Message, command: str):
        """Handle metabot command routing."""
        command = command.strip().lower()
        logger.info(f"Metabot command received: {command} from {message.author}")
        
        if command == "status":
            await self.handle_status(message.channel)
        elif command == "logs":
            await self.handle_logs(message.channel)
        elif command == "restart":
            await self.handle_restart(client, message.channel)
        else:
            await message.channel.send(
                "⚠️ Unknown metabot command.\n"
                "Available commands: `status`, `logs`, `restart`"
            )

