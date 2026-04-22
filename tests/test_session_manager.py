"""Tests for SessionManager."""
import json
import pytest
from handlers.session_manager import SessionManager


@pytest.fixture()
def sessions_file(tmp_path):
    return str(tmp_path / "sessions.json")


@pytest.fixture()
def manager(sessions_file, monkeypatch):
    monkeypatch.setattr("handlers.session_manager.Config.SESSIONS_FILE", sessions_file)
    return SessionManager()


def test_get_session_missing(manager):
    assert manager.get_session(123) == (None, None)


@pytest.mark.asyncio
async def test_set_and_get_session(manager):
    await manager.set_session(123, "sess-abc", "/home/user/projects/foo")
    assert manager.get_session(123) == ("sess-abc", "/home/user/projects/foo")


@pytest.mark.asyncio
async def test_set_session_no_cwd(manager):
    await manager.set_session(123, "sess-abc")
    assert manager.get_session(123) == ("sess-abc", None)


@pytest.mark.asyncio
async def test_set_session_persists(manager, sessions_file, monkeypatch):
    await manager.set_session(456, "sess-xyz", "/home/user/projects/bar")
    monkeypatch.setattr("handlers.session_manager.Config.SESSIONS_FILE", sessions_file)
    manager2 = SessionManager()
    assert manager2.get_session(456) == ("sess-xyz", "/home/user/projects/bar")


@pytest.mark.asyncio
async def test_set_session_none_removes(manager):
    await manager.set_session(123, "sess-abc", "/some/path")
    await manager.set_session(123, None)
    assert manager.get_session(123) == (None, None)


@pytest.mark.asyncio
async def test_set_session_none_missing_key(manager):
    await manager.set_session(999, None)
    assert manager.get_session(999) == (None, None)


def test_load_sessions_invalid_json(sessions_file, monkeypatch):
    with open(sessions_file, "w") as f:
        f.write("not json")
    monkeypatch.setattr("handlers.session_manager.Config.SESSIONS_FILE", sessions_file)
    manager = SessionManager()
    assert manager.sessions == {}


def test_load_sessions_legacy_string_format(sessions_file, monkeypatch):
    """Legacy entries (bare session_id strings) are migrated on load."""
    with open(sessions_file, "w") as f:
        json.dump({"111": "old-session-id"}, f)
    monkeypatch.setattr("handlers.session_manager.Config.SESSIONS_FILE", sessions_file)
    manager = SessionManager()
    assert manager.get_session(111) == ("old-session-id", None)


def test_load_sessions_new_dict_format(sessions_file, monkeypatch):
    with open(sessions_file, "w") as f:
        json.dump({"222": {"session_id": "new-id", "cwd": "/some/path"}}, f)
    monkeypatch.setattr("handlers.session_manager.Config.SESSIONS_FILE", sessions_file)
    manager = SessionManager()
    assert manager.get_session(222) == ("new-id", "/some/path")
