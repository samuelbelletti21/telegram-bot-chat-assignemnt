from app.models.message import Message

class MessageStore:
    def __init__(self):
        self._messages: list[Message] = []

    def get_all(self) -> list[Message]:
        return list(self._messages)

    def add(self, message: Message) -> None:
        self._messages.append(message)