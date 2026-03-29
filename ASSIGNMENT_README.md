# Implementation Notes & Architecture Decisions

## What Was Built

A real-time web chat interface that bridges a React frontend with a Telegram bot, allowing a browser user and a Telegram participant to exchange messages in real time.

---

## Architecture

```
Browser (React)  ←──WebSocket──→  FastAPI backend  ←──python-telegram-bot polling──→  Telegram
```

### Communication: WebSockets

WebSockets were chosen over SSE or long-polling because the channel is **bidirectional** by nature — the browser needs to both send messages and receive them. A persistent full-duplex connection avoids the overhead of repeated HTTP requests and gives instant delivery in both directions.

### Message Flow

| Direction | Path |
|-----------|------|
| Browser → Telegram | `App.jsx` sends `SEND_MESSAGE` event over WS → `handlers.py` validates and calls `TelegramManager.send_to_chat()` → Telegram API |
| Telegram → Browser | python-telegram-bot polling receives update → `TelegramManager.handle_incoming_message()` → `ConnectionManager.broadcast_json()` → all connected WS clients |

### One-Chat Enforcement

`TelegramManager` tracks `active_chat_id`. The first Telegram user who sends a message claims the session; anyone else receives a rejection message from the bot. This fulfils the "single remote participant" requirement.

---

## Design Decisions & Trade-offs

| Decision | Rationale                                                                                                                                 |
|----------|-------------------------------------------------------------------------------------------------------------------------------------------|
| **In-memory message store** | Simplest implementation; sufficient for a single-session demo. Messages are lost on restart.                                              |
| **Session-scoped state** | `active_chat_id` and `MessageStore` live in process memory, A restart resets both.                                                        |
| **Broadcast to all WS clients** | Allows multiple browser tabs to share the same session view. Adding auth or per-user channels is out of scope here.                       |
| **python-telegram-bot polling** | Easier to run locally than a webhook (no public URL needed). |
| **CORS allow-all** | Acceptable for local development. In production, restrict `allow_origins` to the actual frontend domain.                                  |

---

## Running the Project

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in TELEGRAM_BOT_TOKEN
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
