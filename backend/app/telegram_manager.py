from typing import Optional

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes, MessageHandler, filters

from app.connections import ConnectionManager
from app.const import Direction, EventType
from app.models.message import MessageCreate
from app.services import ChatService


class TelegramManager:
    def __init__(
        self,
        token: str,
        chat_service: ChatService,
        connection_manager: ConnectionManager,
    ):
        self.token = token
        self.chat_service = chat_service
        self.connection_manager = connection_manager

        self.active_chat_id: Optional[int] = None
        self.application: Optional[Application] = None

    def ensure_one_active_chat(self, chat_id: int) -> bool:
        if self.active_chat_id is None:
            self.active_chat_id = chat_id
            return True

        return self.active_chat_id == chat_id

    async def send_rejection_message(self, chat_id: int) -> None:
        if self.application is None:
            return

        await self.application.bot.send_message(
            chat_id=chat_id,
            text="This bot is already connected to another active chat.",
        )

    async def send_to_chat(self, text: str) -> None:
        if self.application is None:
            raise RuntimeError("Telegram application is not initialized")

        if self.active_chat_id is None:
            raise RuntimeError("No active Telegram chat connected")

        await self.application.bot.send_message(
            chat_id=self.active_chat_id,
            text=text,
        )

    async def handle_incoming_message(self, chat_id: int, text: str) -> None:
        is_allowed_chat = self.ensure_one_active_chat(chat_id)

        if not is_allowed_chat:
            await self.send_rejection_message(chat_id)
            return

        message_data = MessageCreate(
            text=text,
            direction=Direction.INCOMING,
        )
        new_message = self.chat_service.create_message(message_data)

        await self.connection_manager.broadcast_json({
            "type": EventType.MESSAGE_CREATED,
            "payload": new_message.model_dump(mode="json"),
        })

    async def _telegram_text_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        if update.effective_chat is None:
            return

        if update.effective_message is None:
            return

        text = update.effective_message.text
        if not text:
            return

        await self.handle_incoming_message(
            chat_id=update.effective_chat.id,
            text=text,
        )

    async def start(self) -> None:
        self.application = ApplicationBuilder().token(self.token).build()

        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._telegram_text_handler)
        )

        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

    async def stop(self) -> None:
        if self.application is None:
            return

        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()