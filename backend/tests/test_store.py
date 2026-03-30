import uuid
from datetime import datetime, timezone

from app.models.message import Message
from app.const import Direction


def _make_message(**kwargs) -> Message:
    defaults = dict(
        id=str(uuid.uuid4()),
        text="hello",
        direction=Direction.INCOMING,
        timestamp=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return Message(**defaults)


def test_new_store_is_empty(message_store):
    assert message_store.get_all() == []


def test_add_message(message_store):
    msg = _make_message()
    message_store.add(msg)
    assert len(message_store.get_all()) == 1
    assert message_store.get_all()[0] == msg


def test_get_all_returns_copy(message_store):
    """Mutating the returned list must not affect the store."""
    msg = _make_message()
    message_store.add(msg)
    result = message_store.get_all()
    result.clear()
    assert len(message_store.get_all()) == 1


def test_add_multiple_messages(message_store):
    for i in range(3):
        message_store.add(_make_message(text=f"msg{i}"))
    assert len(message_store.get_all()) == 3


def test_messages_preserve_insertion_order(message_store):
    texts = ["first", "second", "third"]
    for t in texts:
        message_store.add(_make_message(text=t))
    assert [m.text for m in message_store.get_all()] == texts

