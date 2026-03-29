import uuid
from datetime import datetime, timezone
from pydantic import ValidationError

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.models.message import Message, MessageCreate

app = FastAPI(title="Telegram Chat Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Candidate may tighten this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: move ConnectionManager to a separate file
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Connected clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"Connected clients: {len(self.active_connections)}")

    async def broadcast_json(self, message: dict):
        disconnected_connections = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected_connections.append(connection)

        for connection in disconnected_connections:
            self.disconnect(connection)


messages: list[Message] = []
manager = ConnectionManager()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            print("Received:", data)
            message_type = data.get("type")
            payload = data.get("payload", {})

            if message_type == "get_messages":
                await websocket.send_json({
                    "type": "messages_list",
                    "payload": [message.model_dump(mode="json") for message in messages],
                })

            elif message_type == "send_message":
                try:
                    message_data = MessageCreate(**payload)
                except ValidationError as e:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": str(e)},
                    })
                    continue

                new_message = Message.model_validate({
                    **message_data.model_dump(),
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now(timezone.utc),
                })

                messages.append(new_message)

                await websocket.send_json({
                    "type": "message_created",
                    "payload": new_message.model_dump(mode="json"),
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "payload": {
                        "message": f"Unknown event type: {message_type}"
                    },
                })


    except WebSocketDisconnect:
        print("Client disconnected")
        manager.disconnect(websocket)