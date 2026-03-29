from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.connections import ConnectionManager
from app.store import MessageStore
from app.services import ChatService

app = FastAPI(title="Telegram Chat Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Candidate may tighten this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connection_manager = ConnectionManager()
message_store = MessageStore()
chat_service = ChatService(message_store)

async def send_error(websocket: WebSocket, message: str):
    await websocket.send_json({
        "type": "error",
        "payload": {"message": message},
    })

async def handle_get_messages(websocket: WebSocket):
    await websocket.send_json({
        "type": "messages_list",
        "payload": [
            message.model_dump(mode="json")
            for message in chat_service.get_messages()
        ],
    })

async def handle_send_message(websocket: WebSocket, payload: dict):
    try:
        message_data = MessageCreate(**payload)
        new_message = chat_service.create_message(message_data)
    except ValidationError as e:
        await send_error(websocket, str(e))
        return

    await connection_manager.broadcast_json({
        "type": "message_created",
        "payload": new_message.model_dump(mode="json"),
    })

async def handle_client_message(websocket: WebSocket, data: dict):
    message_type = data.get("type")
    payload = data.get("payload", {})

    if message_type == "get_messages":
        await handle_get_messages(websocket)

    elif message_type == "send_message":
        await handle_send_message(websocket, payload)

    else:
        await send_error(websocket, f"Unknown event type: {message_type}")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await handle_client_message(websocket, data)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        print("Client disconnected")