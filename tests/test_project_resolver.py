"""Tests for ProjectResolver path traversal guard."""
import os
import pytest
from unittest.mock import MagicMock, patch
import discord
from utils.project_resolver import ProjectResolver


def _make_channel(topic: str, is_thread: bool = False):
    if is_thread:
        parent = MagicMock(spec=discord.TextChannel)
        parent.topic = topic
        channel = MagicMock(spec=discord.Thread)
        channel.parent = parent
        return channel
    channel = MagicMock(spec=discord.TextChannel)
    channel.topic = topic
    return channel


@pytest.fixture()
def base_dir(tmp_path):
    projects = tmp_path / "projects"
    projects.mkdir()
    (projects / "myapp").mkdir()
    return str(projects)


def test_valid_project(base_dir):
    channel = _make_channel("myapp")
    with patch("utils.project_resolver.Config") as cfg:
        cfg.BASE_DIR = base_dir
        result = ProjectResolver.get_full_project_path(channel)
    assert result == os.path.join(base_dir, "myapp")


def test_path_traversal_blocked(base_dir):
    channel = _make_channel("../secret")
    with patch("utils.project_resolver.Config") as cfg:
        cfg.BASE_DIR = base_dir
        result = ProjectResolver.get_full_project_path(channel)
    assert result is None


def test_deep_traversal_blocked(base_dir):
    channel = _make_channel("myapp/../../etc/passwd")
    with patch("utils.project_resolver.Config") as cfg:
        cfg.BASE_DIR = base_dir
        result = ProjectResolver.get_full_project_path(channel)
    assert result is None


def test_no_topic_returns_none(base_dir):
    channel = _make_channel("")
    with patch("utils.project_resolver.Config") as cfg:
        cfg.BASE_DIR = base_dir
        result = ProjectResolver.get_full_project_path(channel)
    assert result is None


def test_thread_uses_parent_topic(base_dir):
    channel = _make_channel("myapp", is_thread=True)
    with patch("utils.project_resolver.Config") as cfg:
        cfg.BASE_DIR = base_dir
        result = ProjectResolver.get_full_project_path(channel)
    assert result == os.path.join(base_dir, "myapp")
