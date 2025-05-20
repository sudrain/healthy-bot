# 1. Создаем кастомный фильтр (например, в src/filters/admin.py)
from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import Message

# Список ID администраторов(заменить на хранение в базе или окружении)
ADMINS_IDS = [1066332448]


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message, bot: Bot) -> bool:
        return message.from_user.id in ADMINS_IDS
