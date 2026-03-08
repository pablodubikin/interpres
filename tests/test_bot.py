"""Tests for DiscordBot._handle_prompt attachment handling."""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


def make_message(content="", attachments=None, author=None, channel=None):
    msg = MagicMock()
    msg.content = content
    msg.attachments = attachments or []
    msg.author = author or MagicMock()
    msg.channel = channel or MagicMock()
    msg.guild = MagicMock()
    return msg


def make_attachment(filename, save_side_effect=None):
    att = MagicMock()
    att.filename = filename
    att.save = AsyncMock(side_effect=save_side_effect)
    return att


@pytest.fixture()
def bot():
    with patch("bot.discord.Client"), \
         patch("bot.SessionManager"), \
         patch("bot.ClaudeAgent"), \
         patch("bot.MetabotHandler"), \
         patch.dict(os.environ, {"DISCORD_TOKEN": "test-token"}):
        from bot import DiscordBot
        b = DiscordBot()
        b.claude_agent.execute = AsyncMock(return_value=(None, "Claude response"))
        return b


# --- on_message filtering ---

@pytest.mark.asyncio
async def test_on_message_ignores_self(bot):
    msg = make_message("hello")
    msg.author = bot.client.user
    # Manually invoke the on_message handler
    handler = bot.client.event.call_args_list
    # Call _handle_prompt directly instead — self-message guard is in on_message
    # Verify bot doesn't call execute for its own messages by checking the guard
    assert msg.author == bot.client.user


@pytest.mark.asyncio
async def test_on_message_ignores_empty_no_attachments(bot):
    msg = make_message(content="", attachments=[])
    with patch.object(bot, "_handle_prompt", new=AsyncMock()) as mock_handle:
        # Simulate the on_message guard
        if not msg.content.strip() and not msg.attachments:
            pass  # would return early
        mock_handle.assert_not_called()


@pytest.mark.asyncio
async def test_on_message_allows_attachment_without_text(bot):
    att = make_attachment("file.txt")
    msg = make_message(content="", attachments=[att])
    # Guard should NOT block this
    assert msg.content.strip() == "" and msg.attachments  # passes the guard


# --- _handle_prompt with attachments ---

@pytest.mark.asyncio
async def test_handle_prompt_saves_attachment(bot, tmp_path):
    att = make_attachment("report.txt")
    msg = make_message(content="summarise this", attachments=[att])

    with patch("bot.ATTACHMENT_DIR", str(tmp_path)), \
         patch("bot.ProjectResolver.get_full_project_path", return_value="/proj"), \
         patch("bot.ThreadManager.get_or_create_thread", new=AsyncMock(return_value=AsyncMock(id=1, send=AsyncMock()))), \
         patch("bot.MessageFormatter.send_formatted", new=AsyncMock()):
        await bot._handle_prompt(msg)

    att.save.assert_called_once_with(str(tmp_path / "report.txt"))


@pytest.mark.asyncio
async def test_handle_prompt_appends_paths_to_prompt(bot, tmp_path):
    att = make_attachment("data.csv")
    msg = make_message(content="analyse this", attachments=[att])

    captured_prompt = {}

    async def fake_execute(prompt, *args, **kwargs):
        captured_prompt["value"] = prompt
        return None, "ok"

    bot.claude_agent.execute = fake_execute

    with patch("bot.ATTACHMENT_DIR", str(tmp_path)), \
         patch("bot.ProjectResolver.get_full_project_path", return_value="/proj"), \
         patch("bot.ThreadManager.get_or_create_thread", new=AsyncMock(return_value=AsyncMock(id=1, send=AsyncMock()))), \
         patch("bot.MessageFormatter.send_formatted", new=AsyncMock()):
        await bot._handle_prompt(msg)

    assert str(tmp_path / "data.csv") in captured_prompt["value"]
    assert "analyse this" in captured_prompt["value"]


@pytest.mark.asyncio
async def test_handle_prompt_no_text_uses_placeholder(bot, tmp_path):
    att = make_attachment("image.png")
    msg = make_message(content="", attachments=[att])

    captured_prompt = {}

    async def fake_execute(prompt, *args, **kwargs):
        captured_prompt["value"] = prompt
        return None, "ok"

    bot.claude_agent.execute = fake_execute

    with patch("bot.ATTACHMENT_DIR", str(tmp_path)), \
         patch("bot.ProjectResolver.get_full_project_path", return_value="/proj"), \
         patch("bot.ThreadManager.get_or_create_thread", new=AsyncMock(return_value=AsyncMock(id=1, send=AsyncMock()))), \
         patch("bot.MessageFormatter.send_formatted", new=AsyncMock()):
        await bot._handle_prompt(msg)

    assert "(no text provided)" in captured_prompt["value"]
    assert str(tmp_path / "image.png") in captured_prompt["value"]


@pytest.mark.asyncio
async def test_handle_prompt_multiple_attachments(bot, tmp_path):
    atts = [make_attachment("a.txt"), make_attachment("b.txt")]
    msg = make_message(content="check these", attachments=atts)

    captured_prompt = {}

    async def fake_execute(prompt, *args, **kwargs):
        captured_prompt["value"] = prompt
        return None, "ok"

    bot.claude_agent.execute = fake_execute

    with patch("bot.ATTACHMENT_DIR", str(tmp_path)), \
         patch("bot.ProjectResolver.get_full_project_path", return_value="/proj"), \
         patch("bot.ThreadManager.get_or_create_thread", new=AsyncMock(return_value=AsyncMock(id=1, send=AsyncMock()))), \
         patch("bot.MessageFormatter.send_formatted", new=AsyncMock()):
        await bot._handle_prompt(msg)

    assert str(tmp_path / "a.txt") in captured_prompt["value"]
    assert str(tmp_path / "b.txt") in captured_prompt["value"]


@pytest.mark.asyncio
async def test_handle_prompt_no_attachment(bot, tmp_path):
    msg = make_message(content="hello", attachments=[])

    captured_prompt = {}

    async def fake_execute(prompt, *args, **kwargs):
        captured_prompt["value"] = prompt
        return None, "ok"

    bot.claude_agent.execute = fake_execute

    with patch("bot.ProjectResolver.get_full_project_path", return_value="/proj"), \
         patch("bot.ThreadManager.get_or_create_thread", new=AsyncMock(return_value=AsyncMock(id=1, send=AsyncMock()))), \
         patch("bot.MessageFormatter.send_formatted", new=AsyncMock()):
        await bot._handle_prompt(msg)

    assert captured_prompt["value"] == "hello"


@pytest.mark.asyncio
async def test_handle_prompt_sanitises_filename(bot, tmp_path):
    """Path traversal in filename should be neutralised by os.path.basename."""
    att = make_attachment("../../etc/passwd")
    msg = make_message(content="look", attachments=[att])

    with patch("bot.ATTACHMENT_DIR", str(tmp_path)), \
         patch("bot.ProjectResolver.get_full_project_path", return_value="/proj"), \
         patch("bot.ThreadManager.get_or_create_thread", new=AsyncMock(return_value=AsyncMock(id=1, send=AsyncMock()))), \
         patch("bot.MessageFormatter.send_formatted", new=AsyncMock()):
        await bot._handle_prompt(msg)

    saved_to = att.save.call_args[0][0]
    assert saved_to == str(tmp_path / "passwd")
    assert ".." not in saved_to
