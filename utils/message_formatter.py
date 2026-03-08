"""Handles formatting and sending messages to Discord."""
from typing import Optional, List
from config import Config


class MessageFormatter:
    """Handles formatting and sending messages to Discord."""
    
    @staticmethod
    def escape_backticks(text: str) -> str:
        """Escape triple backticks to prevent breaking code blocks."""
        return text.replace("```", "`\u200b`\u200b`")
    
    @staticmethod
    def is_code(text: str) -> bool:
        """Check if text looks like code."""
        return text.strip().startswith(Config.CODE_BLOCK_PREFIXES)
    
    @staticmethod
    def chunk_message(text: str, max_length: int = Config.DISCORD_MAX_MESSAGE_LENGTH) -> List[str]:
        """Split message into chunks if it exceeds max_length."""
        if len(text) <= max_length:
            return [text]
        return [text[i:i+max_length] for i in range(0, len(text), max_length)]
    
    @staticmethod
    async def send_formatted(channel, text: str, language: Optional[str] = None):
        """Send formatted message to Discord channel, chunking if necessary."""
        escaped_text = MessageFormatter.escape_backticks(text)
        
        # Determine if we should use code block formatting
        use_code_block = MessageFormatter.is_code(escaped_text) or language is not None
        
        chunks = MessageFormatter.chunk_message(escaped_text)
        
        for chunk in chunks:
            if use_code_block:
                lang = language or ""
                await channel.send(f"```{lang}\n{chunk}\n```")
            else:
                await channel.send(chunk)

