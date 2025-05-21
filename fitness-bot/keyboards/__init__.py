from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="➕ Добавить тренировку")
    builder.button(text="📊 Аналитика")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Выберите действие")
