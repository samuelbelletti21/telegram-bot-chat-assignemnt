import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.message import Message, MessageCreate
from app.const import Direction


# ---------------------------------------------------------------------------
# MessageCreate
# ---------------------------------------------------------------------------

def test_message_create_valid_incoming():
    msg = MessageCreate(text="hello", direction=Direction.INCOMING)
    assert msg.text == "hello"
    assert msg.direction == Direction.INCOMING


def test_message_create_valid_outgoing():
    msg = MessageCreate(text="hi", direction=Direction.OUTGOING)
    assert msg.direction == Direction.OUTGOING


def test_message_create_empty_text_raises():
    with pytest.raises(ValidationError):
        MessageCreate(text="", direction=Direction.INCOMING)


def test_message_create_whitespace_only_raises():
    with pytest.raises(ValidationError):
        MessageCreate(text="   ", direction=Direction.INCOMING)


def test_message_create_strips_not_applied():
    """Validator rejects whitespace; non-whitespace text is preserved as-is."""
    msg = MessageCreate(text="  hi  ", direction=Direction.INCOMING)
    assert msg.text == "  hi  "


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------

def test_message_model_dump_has_all_fields():
    msg = Message(
        id=str(uuid.uuid4()),
        text="test",
        direction=Direction.INCOMING,
        timestamp=datetime.now(timezone.utc),
    )
    dumped = msg.model_dump()
    assert {"id", "text", "direction", "timestamp"} <= dumped.keys()


def test_message_model_dump_json_mode_serialises_timestamp():
    msg = Message(
        id=str(uuid.uuid4()),
        text="test",
        direction=Direction.OUTGOING,
        timestamp=datetime.now(timezone.utc),
    )
    dumped = msg.model_dump(mode="json")
    # timestamp must be a string (ISO-8601) in JSON mode
    assert isinstance(dumped["timestamp"], str)
    # direction must be the raw string value
    assert dumped["direction"] == "outgoing"

