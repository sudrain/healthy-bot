from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

workout_router = Router()


@workout_router.message(Command("add_workout"))
async def command_add_workout(message: Message) -> None:
    await message.answer("workout")


@workout_router.message(Command("progress"))
async def command_progress(message: Message) -> None:
    await message.answer("progress")
