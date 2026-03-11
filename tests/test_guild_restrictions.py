"""Tests for per-guild path and channel restrictions."""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

class TestConfigGetGuildBaseDir:
    def test_unknown_guild_returns_none(self):
        from config import Config
        with patch.object(Config, "GUILD_BASE_DIRS", {}):
            assert Config.get_guild_base_dir(999) is None

    def test_string_entry_returns_path(self):
        from config import Config
        with patch.object(Config, "GUILD_BASE_DIRS", {"111": "/some/path"}):
            assert Config.get_guild_base_dir(111) == "/some/path"

    def test_dict_entry_returns_base_dir(self):
        from config import Config
        with patch.object(Config, "GUILD_BASE_DIRS", {"111": {"base_dir": "/some/path", "channel_id": 42}}):
            assert Config.get_guild_base_dir(111) == "/some/path"


class TestConfigGetGuildChannelId:
    def test_unknown_guild_returns_none(self):
        from config import Config
        with patch.object(Config, "GUILD_BASE_DIRS", {}):
            assert Config.get_guild_channel_id(999) is None

    def test_string_entry_returns_none(self):
        from config import Config
        with patch.object(Config, "GUILD_BASE_DIRS", {"111": "/some/path"}):
            assert Config.get_guild_channel_id(111) is None

    def test_dict_without_channel_id_returns_none(self):
        from config import Config
        with patch.object(Config, "GUILD_BASE_DIRS", {"111": {"base_dir": "/some/path"}}):
            assert Config.get_guild_channel_id(111) is None

    def test_dict_with_channel_id_returns_it(self):
        from config import Config
        with patch.object(Config, "GUILD_BASE_DIRS", {"111": {"base_dir": "/some/path", "channel_id": 42}}):
            assert Config.get_guild_channel_id(111) == 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bot():
    with patch("bot.discord.Client"), \
         patch("bot.SessionManager"), \
         patch("bot.ClaudeAgent"), \
         patch("bot.MetabotHandler"), \
         patch.dict(os.environ, {"DISCORD_TOKEN": "test-token"}):
        from bot import DiscordBot
        return DiscordBot()


def _make_message(guild_id=None, channel_id=100, is_thread=False, parent_id=None):
    msg = MagicMock(spec=discord.Message)
    if guild_id is not None:
        msg.guild = MagicMock()
        msg.guild.id = guild_id
    else:
        msg.guild = None

    if is_thread:
        channel = MagicMock(spec=discord.Thread)
        parent = MagicMock(spec=discord.TextChannel)
        parent.id = parent_id or channel_id
        channel.parent = parent
        channel.id = channel_id
    else:
        channel = MagicMock(spec=discord.TextChannel)
        channel.id = channel_id

    msg.channel = channel
    return msg


# ---------------------------------------------------------------------------
# _is_message_allowed
# ---------------------------------------------------------------------------

class TestIsMessageAllowed:
    def test_no_guild_dm_rejected(self):
        bot = _make_bot()
        msg = _make_message(guild_id=None)
        assert bot._is_message_allowed(msg) is False

    def test_unknown_guild_rejected(self):
        bot = _make_bot()
        msg = _make_message(guild_id=999)
        with patch("bot.Config.get_guild_base_dir", return_value=None):
            assert bot._is_message_allowed(msg) is False

    def test_known_guild_no_channel_restriction_allowed(self):
        bot = _make_bot()
        msg = _make_message(guild_id=111, channel_id=200)
        with patch("bot.Config.get_guild_base_dir", return_value="/some/path"), \
             patch("bot.Config.get_guild_channel_id", return_value=None):
            assert bot._is_message_allowed(msg) is True

    def test_known_guild_correct_channel_allowed(self):
        bot = _make_bot()
        msg = _make_message(guild_id=111, channel_id=200)
        with patch("bot.Config.get_guild_base_dir", return_value="/some/path"), \
             patch("bot.Config.get_guild_channel_id", return_value=200):
            assert bot._is_message_allowed(msg) is True

    def test_known_guild_wrong_channel_rejected(self):
        bot = _make_bot()
        msg = _make_message(guild_id=111, channel_id=999)
        with patch("bot.Config.get_guild_base_dir", return_value="/some/path"), \
             patch("bot.Config.get_guild_channel_id", return_value=200):
            assert bot._is_message_allowed(msg) is False

    def test_thread_in_allowed_channel_allowed(self):
        bot = _make_bot()
        msg = _make_message(guild_id=111, channel_id=50, is_thread=True, parent_id=200)
        with patch("bot.Config.get_guild_base_dir", return_value="/some/path"), \
             patch("bot.Config.get_guild_channel_id", return_value=200):
            assert bot._is_message_allowed(msg) is True

    def test_thread_in_wrong_channel_rejected(self):
        bot = _make_bot()
        msg = _make_message(guild_id=111, channel_id=50, is_thread=True, parent_id=999)
        with patch("bot.Config.get_guild_base_dir", return_value="/some/path"), \
             patch("bot.Config.get_guild_channel_id", return_value=200):
            assert bot._is_message_allowed(msg) is False


# ---------------------------------------------------------------------------
# _get_guild_base_dir
# ---------------------------------------------------------------------------

class TestGetGuildBaseDir:
    def test_returns_guild_base_dir(self):
        bot = _make_bot()
        msg = _make_message(guild_id=111)
        with patch("bot.Config.get_guild_base_dir", return_value="/guild/path"):
            assert bot._get_guild_base_dir(msg) == "/guild/path"

    def test_falls_back_to_config_base_dir(self):
        from config import Config
        bot = _make_bot()
        msg = _make_message(guild_id=111)
        with patch("bot.Config.get_guild_base_dir", return_value=None):
            assert bot._get_guild_base_dir(msg) == Config.BASE_DIR


# ---------------------------------------------------------------------------
# ProjectResolver with explicit base_dir
# ---------------------------------------------------------------------------

class TestProjectResolverWithBaseDir:
    def test_uses_provided_base_dir(self, tmp_path):
        from utils.project_resolver import ProjectResolver
        import discord as dc

        alt_base = tmp_path / "alt"
        alt_base.mkdir()
        (alt_base / "myapp").mkdir()

        channel = MagicMock(spec=dc.TextChannel)
        channel.topic = "myapp"

        result = ProjectResolver.get_full_project_path(channel, str(alt_base))
        assert result == str(alt_base / "myapp")

    def test_path_traversal_blocked_with_custom_base(self, tmp_path):
        from utils.project_resolver import ProjectResolver
        import discord as dc

        alt_base = tmp_path / "alt"
        alt_base.mkdir()

        channel = MagicMock(spec=dc.TextChannel)
        channel.topic = "../../etc/passwd"

        result = ProjectResolver.get_full_project_path(channel, str(alt_base))
        assert result is None
