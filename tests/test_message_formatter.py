"""Tests for MessageFormatter."""
import pytest
from utils.message_formatter import MessageFormatter


def test_escape_backticks():
    assert "```" not in MessageFormatter.escape_backticks("```python\ncode\n```")


def test_escape_backticks_no_change():
    text = "no backticks here"
    assert MessageFormatter.escape_backticks(text) == text


def test_chunk_message_short():
    text = "hello"
    assert MessageFormatter.chunk_message(text) == ["hello"]


def test_chunk_message_splits():
    text = "a" * 4000
    chunks = MessageFormatter.chunk_message(text, max_length=1900)
    assert len(chunks) == 3
    assert all(len(c) <= 1900 for c in chunks)
    assert "".join(chunks) == text


def test_chunk_message_exact_boundary():
    text = "x" * 1900
    chunks = MessageFormatter.chunk_message(text, max_length=1900)
    assert len(chunks) == 1


def test_is_code_detects_def():
    assert MessageFormatter.is_code("def foo():\n    pass")


def test_is_code_detects_class():
    assert MessageFormatter.is_code("class Foo:")


def test_is_code_detects_import():
    assert MessageFormatter.is_code("import os")


def test_is_code_false_for_prose():
    assert not MessageFormatter.is_code("This is a normal sentence.")


@pytest.mark.asyncio
async def test_send_formatted_plain(mocker):
    channel = mocker.AsyncMock()
    await MessageFormatter.send_formatted(channel, "Hello world")
    channel.send.assert_called_once_with("Hello world")


@pytest.mark.asyncio
async def test_send_formatted_code_block(mocker):
    channel = mocker.AsyncMock()
    await MessageFormatter.send_formatted(channel, "def foo(): pass")
    call_args = channel.send.call_args[0][0]
    assert call_args.startswith("```")


@pytest.mark.asyncio
async def test_send_formatted_chunked(mocker):
    channel = mocker.AsyncMock()
    long_text = "a" * 4000
    await MessageFormatter.send_formatted(channel, long_text)
    assert channel.send.call_count == 3
