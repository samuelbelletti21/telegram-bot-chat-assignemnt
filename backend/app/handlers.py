from fastapi import WebSocket
from pydantic import ValidationError

from app.const import EventType
from app.models.message import MessageCreate
from app.services import ChatService
from app.connections import ConnectionManager

async def send_error(websocket: WebSocket, message: str):
    await websocket.send_json({
        "type": EventType.ERROR,
        "payload": {"message": message},
    })

async def handle_get_messages(websocket: WebSocket, chat_service: ChatService):
    await websocket.send_json({
        "type": EventType.MESSAGES_LIST,
        "payload": [
            message.model_dump(mode="json")
            for message in chat_service.get_messages()
        ],
    })

async def handle_send_message(websocket: WebSocket,
                              payload: dict,
                              chat_service: ChatService,
                              connection_manager: ConnectionManager):
    try:
        message_data = MessageCreate(**payload)
        new_message = chat_service.create_message(message_data)
    except ValidationError as e:
        await send_error(websocket, str(e))
        return

    await connection_manager.broadcast_json({
        "type": EventType.MESSAGE_CREATED,
        "payload": new_message.model_dump(mode="json"),
    })

async def handle_client_message(websocket: WebSocket,
                                data: dict,
                                chat_service: ChatService,
                                connection_manager: ConnectionManager
                                ):
    message_type = data.get("type")
    payload = data.get("payload", {})

    if message_type == EventType.GET_MESSAGES:
        await handle_get_messages(websocket, chat_service)

    elif message_type == EventType.SEND_MESSAGE:
        await handle_send_message(websocket, payload, chat_service, connection_manager)

    else:
        await send_error(websocket, f"Unknown event type: {message_type}")
