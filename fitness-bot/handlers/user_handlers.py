from aiogram import Router, html, types
from aiogram.filters import Command
from aiogram.types import Message

user_router = Router()


@user_router.message(Command("myid"))
async def get_id(message: types.Message):
    await message.answer(f"Ваш ID: {message.from_user.id}")


@user_router.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")
