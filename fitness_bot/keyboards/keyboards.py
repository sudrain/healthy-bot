import asyncpg
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="➕ Добавить тренировку")
    builder.button(text="📊 сейчас не работает")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Выберите действие")


async def get_workout_type_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа тренировки"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🏃 Кардио", callback_data="workout_type:cardio"),
        InlineKeyboardButton(text="🏋️ Силовая", callback_data="workout_type:strength"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
    )
    builder.adjust(2)
    return builder.as_markup()


async def get_exercises_kb(pool: asyncpg.Pool, category: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора упражнений"""
    async with pool.acquire() as conn:
        exercises = await conn.fetch(
            "SELECT id, name FROM exercise_types WHERE category = $1", category
        )

    builder = InlineKeyboardBuilder()
    for ex in exercises:
        builder.add(InlineKeyboardButton(text=ex["name"], callback_data=f"exercise:{ex['id']}"))
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    builder.adjust(2)
    return builder.as_markup()


def get_number_input_kb(param_name: str, current_value: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура для ввода числовых значений"""
    builder = InlineKeyboardBuilder()

    # Кнопки изменения значения
    for delta in [-10, -5, -1, +1, +5, +10]:
        builder.add(
            InlineKeyboardButton(text=f"{delta:+}", callback_data=f"adjust:{param_name}:{delta}")
        )

    # Кнопка подтверждения
    builder.add(
        InlineKeyboardButton(
            text=f"✅ Подтвердить ({current_value})", callback_data=f"confirm_value:{param_name}"
        )
    )

    builder.adjust(3, 3, 1)
    return builder.as_markup()


def get_confirmation_kb() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения упражнения"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_exercise"),
        InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_exercise"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"),
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def get_add_another_kb() -> InlineKeyboardMarkup:
    """Клавиатура для добавления нового упражнения"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="➕ Добавить упражнение", callback_data="add_another"),
        InlineKeyboardButton(text="✅ Завершить тренировку", callback_data="finish_workout"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"),
    )
    builder.adjust(1, 1, 1)
    return builder.as_markup()
