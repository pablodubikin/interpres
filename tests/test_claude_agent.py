"""Tests for ClaudeAgent parsing helpers."""
import json
import pytest
from unittest.mock import MagicMock
from handlers.claude_agent import ClaudeAgent


@pytest.fixture()
def agent():
    session_manager = MagicMock()
    session_manager.get_session.return_value = (None, None)
    return ClaudeAgent(session_manager)


# --- _parse_response ---

def test_parse_response_valid_json(agent):
    stdout = json.dumps({"session_id": "new-sess", "result": "Hello!"})
    session_id, text = agent._parse_response(stdout, "", "old-sess")
    assert session_id == "new-sess"
    assert text == "Hello!"


def test_parse_response_uses_existing_session_when_missing(agent):
    stdout = json.dumps({"result": "Hi"})
    session_id, text = agent._parse_response(stdout, "", "old-sess")
    assert session_id == "old-sess"


def test_parse_response_empty_result_gives_warning(agent):
    stdout = json.dumps({"session_id": "s", "result": ""})
    _, text = agent._parse_response(stdout, "", None)
    assert "⚠️" in text


def test_parse_response_invalid_json_falls_back_to_stdout(agent):
    session_id, text = agent._parse_response("raw output", "", "old-sess")
    assert text == "raw output"
    assert session_id == "old-sess"


def test_parse_response_invalid_json_falls_back_to_stderr(agent):
    _, text = agent._parse_response("", "error msg", None)
    assert text == "error msg"


def test_parse_response_nothing_returns_default(agent):
    _, text = agent._parse_response("", "", None)
    assert text == "No response received."


# --- _clean_commit_message ---

def test_clean_commit_message_strips_code_block(agent):
    msg = "```\nfix: update readme\n```"
    assert agent._clean_commit_message(msg) == "fix: update readme"


def test_clean_commit_message_strips_fenced_with_lang(agent):
    msg = "```text\nfeat: add tests\n```"
    assert agent._clean_commit_message(msg) == "feat: add tests"


def test_clean_commit_message_plain_unchanged(agent):
    msg = "feat: add tests"
    assert agent._clean_commit_message(msg) == "feat: add tests"


def test_clean_commit_message_strips_whitespace(agent):
    msg = "  fix: typo  "
    assert agent._clean_commit_message(msg) == "fix: typo"
