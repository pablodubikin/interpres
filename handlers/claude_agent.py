"""Handles interactions with Claude Code subprocess."""
import asyncio
import json
import os
from typing import Optional, Tuple
from .session_manager import SessionManager
from config import logger

SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "system_prompt.md")


class ClaudeAgent:
    """Handles interactions with Claude Code subprocess."""

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    def _parse_response(self, stdout: str, stderr: str, existing_session_id: Optional[str]) -> Tuple[Optional[str], str]:
        """Parse Claude Code JSON response."""
        try:
            data = json.loads(stdout)
            new_session_id = data.get("session_id", existing_session_id)
            output_text = data.get("result", "")
            if not output_text:
                output_text = "⚠️ Received response but couldn't extract text content."
            return new_session_id, output_text
        except json.JSONDecodeError:
            output_text = stdout or stderr or "No response received."
            return existing_session_id, output_text

    def _clean_commit_message(self, message: str) -> str:
        """Clean up commit message (remove code blocks, extra whitespace)."""
        message = message.strip()
        if message.startswith("```"):
            lines = message.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            message = "\n".join(lines).strip()
        return message

    async def _run_claude(self, prompt: str, project_root: str, cwd: str,
                          session_id: Optional[str], system_prompt: str) -> Tuple[str, str]:
        """Run the claude subprocess and return (stdout, stderr)."""
        cmd = [
            "claude", "-p", prompt,
            "--output-format", "json",
            "--add-dir", project_root,
            "--dangerously-skip-permissions",  # Required for non-interactive/headless use; bot runs in a controlled environment
        ]
        if system_prompt:
            cmd += ["--append-system-prompt", system_prompt]
        if session_id:
            cmd += ["--resume", session_id]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        return (stdout_bytes.decode() if stdout_bytes else ""), (stderr_bytes.decode() if stderr_bytes else "")

    async def execute(self, prompt: str, project_root: str, thread_id: int,
                     context_name: str = "Claude Response") -> Tuple[Optional[str], str]:
        """Execute Claude Code command and return session ID and output."""
        session_id, session_cwd = self.session_manager.get_session(thread_id)

        # Use the parent projects directory as cwd for new sessions.
        # Claude Code only loads global MCP servers when cwd is outside any git repo.
        # The project is still accessible via --add-dir above.
        base_dir = os.path.dirname(project_root.rstrip("/"))

        # When resuming, use the cwd the session was originally created under so that
        # Claude Code can find the session in its local project-scoped storage.
        resume_cwd = session_cwd or base_dir

        system_prompt = ""
        if os.path.exists(SYSTEM_PROMPT_PATH):
            with open(SYSTEM_PROMPT_PATH) as f:
                system_prompt = f.read()
            system_prompt = system_prompt.replace("{{THREAD_ID}}", str(thread_id))
            system_prompt = system_prompt.replace("{{PROJECT_ROOT}}", project_root)

        stdout, stderr = await self._run_claude(prompt, project_root, resume_cwd, session_id, system_prompt)

        # If the stored session no longer exists (e.g. Claude purged it or the cwd
        # lookup returned null for a legacy entry), retry as a fresh conversation.
        if session_id and "No conversation found with session ID" in (stdout + stderr):
            logger.warning(f"Stale session {session_id} for thread {thread_id} — retrying fresh")
            await self.session_manager.set_session(thread_id, None)
            session_id = None
            stdout, stderr = await self._run_claude(prompt, project_root, base_dir, None, system_prompt)
            resume_cwd = base_dir

        new_session_id, output_text = self._parse_response(stdout, stderr, session_id)

        # New sessions are always stored with base_dir as their cwd.
        # Resumed sessions keep their original cwd so they remain reachable.
        stored_cwd = resume_cwd if new_session_id == session_id else base_dir
        await self.session_manager.set_session(thread_id, new_session_id, stored_cwd)

        prompt_display = prompt[:50] + "..." if len(prompt) > 50 else prompt
        response_preview = output_text[:200] + "..." if len(output_text) > 200 else output_text
        logger.info(f"Claude executed: '{prompt_display}' | session={new_session_id} | cwd={stored_cwd} | response_len={len(output_text)}")
        logger.debug(f"Claude response preview: {response_preview}")

        if stderr:
            logger.warning(f"Claude stderr: {stderr[:500]}")

        return new_session_id, output_text

    async def generate_commit_message(self, git_diff: str, project_root: str, thread_id: int) -> Optional[str]:
        """Generate commit message from git diff."""
        prompt = f"Please generate a concise, conventional commit message for the following git diff. Only return the commit message, nothing else:\n\n{git_diff}"
        new_session_id, commit_message = await self.execute(
            prompt, project_root, thread_id, "Claude Response (Git Commit Message Generation)"
        )
        if not commit_message:
            return None
        return self._clean_commit_message(commit_message)
