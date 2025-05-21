from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from keyboards import main_menu
from states import WorkoutForm

user_router = Router()


@user_router.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "🏋️ Добро пожаловать в FitnessBot!\nИспользуйте кнопки ниже для навигации:",
        reply_markup=main_menu(),
    )


@user_router.message(F.text.lower() == "➕ добавить тренировку")
async def add_workout_button(message: types.Message, state: FSMContext):
    await message.answer("Запуск добавления тренировки...")
    await state.set_state(WorkoutForm.select_workout_type)
    await message.answer(
        "Выберите тип тренировки:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Силовая")],
                [types.KeyboardButton(text="Кардио")],
            ],
            resize_keboard=True,
        ),
    )


@user_router.message(F.text.lower() == "📊 аналитика")
async def analytics_button(message: types.Message):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="История", callback_data="history")],
            [InlineKeyboardButton(text="Статистика", callback_data="stats")],
            [InlineKeyboardButton(text="Графики", callback_data="charts")],
        ]
    )
    await message.answer("📈 Выберите тип аналитики:", reply_markup=markup)
