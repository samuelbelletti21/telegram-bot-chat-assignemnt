from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.connections import ConnectionManager
from app.store import MessageStore
from app.services import ChatService
from app.handlers import handle_client_message
from app.telegram_manager import TelegramManager
from app.config import TELEGRAM_BOT_TOKEN


connection_manager = ConnectionManager()
message_store = MessageStore()
chat_service = ChatService(message_store)
telegram_manager = TelegramManager(
    token=TELEGRAM_BOT_TOKEN,
    chat_service=chat_service,
    connection_manager=connection_manager,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_manager.start()
    try:
        yield
    finally:
        await telegram_manager.stop()

app = FastAPI(
    title="Telegram Chat Backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Candidate may tighten this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)

    try:
        while True:
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                raise
            except Exception:
                await websocket.send_json({
                    "type": "error",
                    "payload": {"message": "Invalid JSON payload"},
                })
                continue

            await handle_client_message(
                websocket=websocket,
                data=data,
                chat_service=chat_service,
                connection_manager=connection_manager,
                telegram_manager=telegram_manager,
            )
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        print("Client disconnected")