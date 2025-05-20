import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from handlers.admin_handlers import admin_router
from handlers.user_handlers import user_router
from handlers.workout_handlers import workout_router
from middlewares.admin_logger import AdminLoggingMiddleware

# Bot token can be obtained via https://t.me/BotFather
load_dotenv()
TOKEN = getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()
dp.include_routers(admin_router, workout_router, user_router)
dp.message.middleware.register(AdminLoggingMiddleware())


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
