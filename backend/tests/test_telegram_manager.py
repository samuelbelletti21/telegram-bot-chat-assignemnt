from unittest.mock import AsyncMock, MagicMock

import pytest

from app.const import Direction, EventType


# ---------------------------------------------------------------------------
# ensure_one_active_chat
# ---------------------------------------------------------------------------

def test_first_chat_is_accepted(telegram_manager):
    assert telegram_manager.ensure_one_active_chat(111) is True
    assert telegram_manager.active_chat_id == 111


def test_same_chat_is_accepted(telegram_manager):
    telegram_manager.ensure_one_active_chat(111)
    assert telegram_manager.ensure_one_active_chat(111) is True


def test_different_chat_is_rejected(telegram_manager):
    telegram_manager.ensure_one_active_chat(111)
    assert telegram_manager.ensure_one_active_chat(222) is False


def test_active_chat_id_not_overwritten_on_rejection(telegram_manager):
    telegram_manager.ensure_one_active_chat(111)
    telegram_manager.ensure_one_active_chat(222)
    assert telegram_manager.active_chat_id == 111


# ---------------------------------------------------------------------------
# send_to_chat
# ---------------------------------------------------------------------------

async def test_send_to_chat_raises_when_no_application(telegram_manager):
    with pytest.raises(RuntimeError, match="not initialized"):
        await telegram_manager.send_to_chat("hi")


async def test_send_to_chat_raises_when_no_active_chat(telegram_manager):
    telegram_manager.application = MagicMock()
    with pytest.raises(RuntimeError, match="No active Telegram chat"):
        await telegram_manager.send_to_chat("hi")


async def test_send_to_chat_calls_bot_send_message(telegram_manager):
    mock_app = MagicMock()
    mock_app.bot.send_message = AsyncMock()
    telegram_manager.application = mock_app
    telegram_manager.active_chat_id = 42

    await telegram_manager.send_to_chat("hello")

    mock_app.bot.send_message.assert_called_once_with(chat_id=42, text="hello")


# ---------------------------------------------------------------------------
# send_rejection_message
# ---------------------------------------------------------------------------

async def test_send_rejection_message_does_nothing_without_application(telegram_manager):
    # Should not raise when application is None
    await telegram_manager.send_rejection_message(999)


async def test_send_rejection_message_sends_to_chat(telegram_manager):
    mock_app = MagicMock()
    mock_app.bot.send_message = AsyncMock()
    telegram_manager.application = mock_app

    await telegram_manager.send_rejection_message(999)

    mock_app.bot.send_message.assert_called_once()
    call_kwargs = mock_app.bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 999


# ---------------------------------------------------------------------------
# handle_incoming_message
# ---------------------------------------------------------------------------

async def test_handle_incoming_first_message_accepted(telegram_manager):
    telegram_manager.connection_manager.broadcast_json = AsyncMock()

    await telegram_manager.handle_incoming_message(chat_id=10, text="hi")

    assert telegram_manager.active_chat_id == 10
    telegram_manager.connection_manager.broadcast_json.assert_called_once()
    payload = telegram_manager.connection_manager.broadcast_json.call_args[0][0]
    assert payload["type"] == EventType.MESSAGE_CREATED
    assert payload["payload"]["text"] == "hi"
    assert payload["payload"]["direction"] == Direction.INCOMING


async def test_handle_incoming_message_is_stored(telegram_manager, chat_service):
    telegram_manager.connection_manager.broadcast_json = AsyncMock()

    await telegram_manager.handle_incoming_message(chat_id=10, text="stored")

    messages = chat_service.get_messages()
    assert len(messages) == 1
    assert messages[0].text == "stored"


async def test_handle_incoming_different_chat_is_rejected(telegram_manager):
    telegram_manager.active_chat_id = 10
    telegram_manager.send_rejection_message = AsyncMock()
    telegram_manager.connection_manager.broadcast_json = AsyncMock()

    await telegram_manager.handle_incoming_message(chat_id=99, text="intruder")

    telegram_manager.send_rejection_message.assert_called_once_with(99)
    telegram_manager.connection_manager.broadcast_json.assert_not_called()


async def test_handle_incoming_rejected_message_not_stored(telegram_manager, chat_service):
    telegram_manager.active_chat_id = 10
    telegram_manager.send_rejection_message = AsyncMock()

    await telegram_manager.handle_incoming_message(chat_id=99, text="intruder")

    assert chat_service.get_messages() == []

