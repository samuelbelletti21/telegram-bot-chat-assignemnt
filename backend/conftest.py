import os

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")

import pytest

from app.store import MessageStore
from app.services import ChatService
from app.connections import ConnectionManager
from app.telegram_manager import TelegramManager


@pytest.fixture
def message_store():
    return MessageStore()


@pytest.fixture
def chat_service(message_store):
    return ChatService(message_store)


@pytest.fixture
def connection_manager():
    return ConnectionManager()


@pytest.fixture
def telegram_manager(chat_service, connection_manager):
    return TelegramManager(
        token="test_token",
        chat_service=chat_service,
        connection_manager=connection_manager,
    )

