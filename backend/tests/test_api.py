"""
Integration tests for the FastAPI WebSocket endpoint.

The Telegram bot's start/stop are patched so no real network calls are made.
Module-level state (message store, active_chat_id) is reset between tests via
the test_client fixture.
"""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.const import EventType


@pytest.fixture()
def test_client():
    """Return a TestClient with the Telegram manager lifecycle mocked out."""
    # Reset shared in-process state so tests don't bleed into each other.
    main_module.message_store._messages.clear()
    main_module.telegram_manager.active_chat_id = None
    main_module.telegram_manager.application = None

    with (
        patch.object(main_module.telegram_manager, "start", new_callable=AsyncMock),
        patch.object(main_module.telegram_manager, "stop", new_callable=AsyncMock),
    ):
        with TestClient(main_module.app) as client:
            yield client


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def test_health_endpoint(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# WebSocket – basic protocol
# ---------------------------------------------------------------------------

def test_websocket_get_messages_empty(test_client):
    with test_client.websocket_connect("/ws") as ws:
        ws.send_json({"type": EventType.GET_MESSAGES})
        data = ws.receive_json()

    assert data["type"] == EventType.MESSAGES_LIST
    assert data["payload"] == []


def test_websocket_unknown_event_type_returns_error(test_client):
    with test_client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "no_such_event"})
        data = ws.receive_json()

    assert data["type"] == EventType.ERROR


def test_websocket_invalid_json_returns_error(test_client):
    with test_client.websocket_connect("/ws") as ws:
        ws.send_text("{ this is not json }")
        data = ws.receive_json()

    assert data["type"] == EventType.ERROR


# ---------------------------------------------------------------------------
# WebSocket – send message without an active Telegram chat
# ---------------------------------------------------------------------------

def test_websocket_send_message_no_active_chat_returns_error(test_client):
    with test_client.websocket_connect("/ws") as ws:
        ws.send_json({"type": EventType.SEND_MESSAGE, "payload": {"text": "hello"}})
        data = ws.receive_json()

    assert data["type"] == EventType.ERROR


def test_websocket_send_empty_message_returns_error(test_client):
    with test_client.websocket_connect("/ws") as ws:
        ws.send_json({"type": EventType.SEND_MESSAGE, "payload": {"text": ""}})
        data = ws.receive_json()

    assert data["type"] == EventType.ERROR


# ---------------------------------------------------------------------------
# WebSocket – full send-message flow (active chat mocked)
# ---------------------------------------------------------------------------

def test_websocket_send_message_success(test_client):
    main_module.telegram_manager.active_chat_id = 999
    # patch.object ensures send_to_chat is restored after this test,
    # preventing state from leaking into tests that rely on the real implementation.
    with patch.object(main_module.telegram_manager, "send_to_chat", new_callable=AsyncMock):
        with test_client.websocket_connect("/ws") as ws:
            ws.send_json({"type": EventType.SEND_MESSAGE, "payload": {"text": "hey"}})
            data = ws.receive_json()

    assert data["type"] == EventType.MESSAGE_CREATED
    assert data["payload"]["text"] == "hey"
    assert data["payload"]["direction"] == "outgoing"


def test_websocket_sent_message_appears_in_get_messages(test_client):
    main_module.telegram_manager.active_chat_id = 999
    with patch.object(main_module.telegram_manager, "send_to_chat", new_callable=AsyncMock):
        with test_client.websocket_connect("/ws") as ws:
            ws.send_json({"type": EventType.SEND_MESSAGE, "payload": {"text": "stored?"}})
            ws.receive_json()  # MESSAGE_CREATED

            ws.send_json({"type": EventType.GET_MESSAGES})
            data = ws.receive_json()

    assert data["type"] == EventType.MESSAGES_LIST
    assert len(data["payload"]) == 1
    assert data["payload"][0]["text"] == "stored?"

