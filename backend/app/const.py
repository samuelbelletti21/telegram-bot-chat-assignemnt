from enum import Enum

class EventType(str, Enum):
    GET_MESSAGES = "get_messages"
    SEND_MESSAGE = "send_message"

    MESSAGES_LIST = "messages_list"
    MESSAGE_CREATED = "message_created"
    ERROR = "error"

class Direction(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"
