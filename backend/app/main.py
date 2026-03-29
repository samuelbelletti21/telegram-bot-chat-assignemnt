from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.connections import ConnectionManager
from app.store import MessageStore
from app.services import ChatService
from app.handlers import handle_client_message

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

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await handle_client_message(websocket=websocket,
                                        data=data,
                                        chat_service=chat_service,
                                        connection_manager=connection_manager)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        print("Client disconnected")