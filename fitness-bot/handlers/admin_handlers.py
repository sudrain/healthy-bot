from aiogram import Router, types
from aiogram.filters import Command
from filters.admin_filter import IsAdmin

admin_router = Router()


@admin_router.message(Command("admin"), IsAdmin())
async def admin_panel(message: types.Message):
    await message.answer("Привет админ")
