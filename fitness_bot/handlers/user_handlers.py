from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.keyboards import main_menu
from states import WorkoutForm

user_router = Router()


@user_router.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "🏋️ Добро пожаловать в FitnessBot!\nИспользуйте кнопки ниже для навигации:",
        reply_markup=main_menu(),
    )


@user_router.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏋️ Добро пожаловать в FitnessBot!\nИспользуйте кнопки ниже для навигации:",
        reply_markup=main_menu(),
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


@user_router.message(F.text.lower() == "➕ добавить тренировку")
async def start_workout(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Начать тренировку", callback_data="add_workout")
    await state.set_state(WorkoutForm.select_workout_type)
    await message.answer("Выберите действие:", reply_markup=builder.as_markup())
