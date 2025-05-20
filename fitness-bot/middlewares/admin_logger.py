import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from filters.admin_filter import ADMINS_IDS

logger = logging.getLogger(__name__)


class AdminLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Проверяем, является ли пользователь админом
        if event.from_user.id in ADMINS_IDS:
            logger.info(
                f"Admin action: {event.from_user.full_name} (ID: {event.from_user.id})\n"
                f"TypeContent: {event.content_type}\n"
                f"Command: {event.text}"
            )

        # Передаем управление следующему middleware/handler
        return await handler(event, data)
