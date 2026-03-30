from app.models.message import MessageCreate
from app.const import Direction


def test_get_messages_initially_empty(chat_service):
    assert chat_service.get_messages() == []


def test_create_message_returns_message(chat_service):
    msg = chat_service.create_message(MessageCreate(text="hello", direction=Direction.OUTGOING))
    assert msg.text == "hello"
    assert msg.direction == Direction.OUTGOING


def test_create_message_assigns_unique_id(chat_service):
    data = MessageCreate(text="hello", direction=Direction.INCOMING)
    msg1 = chat_service.create_message(data)
    msg2 = chat_service.create_message(data)
    assert msg1.id != msg2.id


def test_create_message_assigns_timestamp(chat_service):
    msg = chat_service.create_message(MessageCreate(text="hi", direction=Direction.INCOMING))
    assert msg.timestamp is not None


def test_create_message_is_persisted(chat_service):
    chat_service.create_message(MessageCreate(text="hello", direction=Direction.INCOMING))
    assert len(chat_service.get_messages()) == 1


def test_create_multiple_messages_all_persisted(chat_service):
    for i in range(5):
        chat_service.create_message(MessageCreate(text=f"msg{i}", direction=Direction.INCOMING))
    assert len(chat_service.get_messages()) == 5


def test_get_messages_preserves_order(chat_service):
    texts = ["a", "b", "c"]
    for t in texts:
        chat_service.create_message(MessageCreate(text=t, direction=Direction.INCOMING))
    assert [m.text for m in chat_service.get_messages()] == texts

