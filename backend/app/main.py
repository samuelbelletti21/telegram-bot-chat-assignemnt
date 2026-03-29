import uuid
from datetime import datetime, timezone

from fastapi import FastAPI
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

messages: list[Message] = []

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/messages", response_model=list[Message])
async def get_messages():
    return messages


@app.post("/messages", response_model=Message)
async def create_message(payload: MessageCreate):
    message = Message(
        id=str(uuid.uuid4()),
        text=payload.text,
        direction=payload.direction,
        timestamp=datetime.now(timezone.utc),
    )

    messages.append(message)

    return message
