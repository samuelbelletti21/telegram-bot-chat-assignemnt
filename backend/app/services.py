import uuid
from datetime import datetime, timezone

from app.models.message import Message, MessageCreate
from app.store import MessageStore

class ChatService:
    def __init__(self, message_store: MessageStore):
        self.message_store = message_store

    def get_messages(self) -> list[Message]:
        return self.message_store.get_all()

    def create_message(self, message_data: MessageCreate) -> Message:
        new_message = Message.model_validate({
            **message_data.model_dump(),
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc),
        })

        self.message_store.add(new_message)
        return new_message