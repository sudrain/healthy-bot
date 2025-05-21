import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from database.core import create_pool
from dotenv import load_dotenv
from handlers.admin_handlers import admin_router
from handlers.user_handlers import user_router
from handlers.workout_handlers import workout_router
from middlewares.admin_logger import AdminLoggingMiddleware

load_dotenv()
TOKEN = getenv("BOT_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),  # Логи в файл
        logging.StreamHandler(),  # Логи в консоль
    ],
)


dp = Dispatcher()
dp.include_routers(admin_router, workout_router, user_router)
dp.message.middleware.register(AdminLoggingMiddleware())


async def main() -> None:
    pool = await create_pool()
    dp["pool"] = pool
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
