from unittest.mock import AsyncMock

import pytest

from app.const import Direction, EventType
from app.handlers import handle_client_message, handle_get_messages, handle_send_message
from app.models.message import MessageCreate


@pytest.fixture
def mock_ws():
    return AsyncMock()


# ---------------------------------------------------------------------------
# handle_get_messages
# ---------------------------------------------------------------------------

async def test_handle_get_messages_returns_empty_list(mock_ws, chat_service):
    await handle_get_messages(mock_ws, chat_service)

    mock_ws.send_json.assert_called_once()
    response = mock_ws.send_json.call_args[0][0]
    assert response["type"] == EventType.MESSAGES_LIST
    assert response["payload"] == []


async def test_handle_get_messages_returns_existing_messages(mock_ws, chat_service):
    chat_service.create_message(MessageCreate(text="hi", direction=Direction.INCOMING))

    await handle_get_messages(mock_ws, chat_service)

    response = mock_ws.send_json.call_args[0][0]
    assert response["type"] == EventType.MESSAGES_LIST
    assert len(response["payload"]) == 1
    assert response["payload"][0]["text"] == "hi"


# ---------------------------------------------------------------------------
# handle_send_message
# ---------------------------------------------------------------------------

async def test_handle_send_message_empty_text_sends_error(
    mock_ws, chat_service, connection_manager, telegram_manager
):
    await handle_send_message(
        mock_ws, {"text": ""}, chat_service, connection_manager, telegram_manager
    )

    response = mock_ws.send_json.call_args[0][0]
    assert response["type"] == EventType.ERROR


async def test_handle_send_message_whitespace_text_sends_error(
    mock_ws, chat_service, connection_manager, telegram_manager
):
    await handle_send_message(
        mock_ws, {"text": "   "}, chat_service, connection_manager, telegram_manager
    )

    response = mock_ws.send_json.call_args[0][0]
    assert response["type"] == EventType.ERROR


async def test_handle_send_message_no_active_chat_sends_error(
    mock_ws, chat_service, connection_manager, telegram_manager
):
    telegram_manager.send_to_chat = AsyncMock(
        side_effect=RuntimeError("No active Telegram chat connected")
    )

    await handle_send_message(
        mock_ws, {"text": "hello"}, chat_service, connection_manager, telegram_manager
    )

    response = mock_ws.send_json.call_args[0][0]
    assert response["type"] == EventType.ERROR


async def test_handle_send_message_success_broadcasts(
    mock_ws, chat_service, connection_manager, telegram_manager
):
    telegram_manager.send_to_chat = AsyncMock()
    connection_manager.broadcast_json = AsyncMock()

    await handle_send_message(
        mock_ws, {"text": "hello"}, chat_service, connection_manager, telegram_manager
    )

    telegram_manager.send_to_chat.assert_called_once_with("hello")
    connection_manager.broadcast_json.assert_called_once()
    broadcast = connection_manager.broadcast_json.call_args[0][0]
    assert broadcast["type"] == EventType.MESSAGE_CREATED
    assert broadcast["payload"]["text"] == "hello"
    assert broadcast["payload"]["direction"] == Direction.OUTGOING


async def test_handle_send_message_success_stores_message(
    mock_ws, chat_service, connection_manager, telegram_manager
):
    telegram_manager.send_to_chat = AsyncMock()
    connection_manager.broadcast_json = AsyncMock()

    await handle_send_message(
        mock_ws, {"text": "hello"}, chat_service, connection_manager, telegram_manager
    )

    assert len(chat_service.get_messages()) == 1


# ---------------------------------------------------------------------------
# handle_client_message (routing)
# ---------------------------------------------------------------------------

async def test_handle_client_message_routes_get_messages(
    mock_ws, chat_service, connection_manager, telegram_manager
):
    await handle_client_message(
        mock_ws, {"type": EventType.GET_MESSAGES}, chat_service, connection_manager, telegram_manager
    )

    response = mock_ws.send_json.call_args[0][0]
    assert response["type"] == EventType.MESSAGES_LIST


async def test_handle_client_message_routes_send_message(
    mock_ws, chat_service, connection_manager, telegram_manager
):
    telegram_manager.send_to_chat = AsyncMock()
    connection_manager.broadcast_json = AsyncMock()

    await handle_client_message(
        mock_ws,
        {"type": EventType.SEND_MESSAGE, "payload": {"text": "hello"}},
        chat_service,
        connection_manager,
        telegram_manager,
    )

    connection_manager.broadcast_json.assert_called_once()


async def test_handle_client_message_unknown_type_sends_error(
    mock_ws, chat_service, connection_manager, telegram_manager
):
    await handle_client_message(
        mock_ws, {"type": "totally_unknown"}, chat_service, connection_manager, telegram_manager
    )

    response = mock_ws.send_json.call_args[0][0]
    assert response["type"] == EventType.ERROR


async def test_handle_client_message_missing_type_sends_error(
    mock_ws, chat_service, connection_manager, telegram_manager
):
    await handle_client_message(
        mock_ws, {}, chat_service, connection_manager, telegram_manager
    )

    response = mock_ws.send_json.call_args[0][0]
    assert response["type"] == EventType.ERROR

