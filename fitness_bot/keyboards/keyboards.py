import asyncpg
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="➕ Добавить тренировку")
    builder.button(text="📊 сейчас не работает")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Выберите действие")


def cancel_button() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отмена")
    return builder.as_markup(resize_keyboard=True)


async def get_type_exercises() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Кардио")
    builder.button(text="Силовая")
    builder.button(text="❌ Отмена")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


async def get_cardio_exercises(pool: asyncpg.Pool) -> ReplyKeyboardMarkup:
    async with pool.acquire() as conn:
        exercises = await conn.fetch("SELECT name FROM exercise_types WHERE category = 'cardio'")

    builder = ReplyKeyboardBuilder()
    for ex in exercises:
        builder.button(text=ex["name"])
    builder.button(text="❌ Отмена")
    builder.adjust(2)
    return builder.as_markup(
        resize_keyboard=True, input_field_placeholder="Выберите кардио-упражнение..."
    )


async def get_strength_exercises(pool: asyncpg.Pool) -> ReplyKeyboardMarkup:
    async with pool.acquire() as conn:
        exercises = await conn.fetch("SELECT name FROM exercise_types WHERE category = 'strength'")

    builder = ReplyKeyboardBuilder()
    for ex in exercises:
        builder.button(text=ex["name"])
    builder.button(text="❌ Отмена")
    builder.adjust(2)
    return builder.as_markup(
        resize_keyboard=True, input_field_placeholder="Выберите силовое упражнение..."
    )


def speed_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="8.5")
    builder.button(text="10.0")
    builder.button(text="12.5")
    builder.button(text="15.0")
    builder.button(text="❌ Отмена")
    builder.adjust(2)
    return builder.as_markup(
        resize_keyboard=True, input_field_placeholder="Выберите или введите скорость..."
    )
