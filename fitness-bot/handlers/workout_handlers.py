from datetime import datetime

import asyncpg
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import main_menu
from states import WorkoutForm

workout_router = Router()


@workout_router.message(WorkoutForm.select_workout_type)
async def process_workout_type(message: types.Message, state: FSMContext):
    await state.update_data(workout_type=message.text)
    await message.answer(
        "Введите продолжительность (в минутах):", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(WorkoutForm.enter_duration)


@workout_router.message(WorkoutForm.enter_duration)
async def process_duration(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите число!")
        return

    await state.update_data(duration=int(message.text))
    await message.answer("Введите дату тренировки (ДД.ММ.ГГГГ):")
    await state.set_state(WorkoutForm.enter_date)


@workout_router.message(WorkoutForm.enter_date)
async def process_date(message: types.Message, state: FSMContext):
    try:
        date_obj = datetime.strptime(message.text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("❌ Неверный формат даты! Используйте ДД.ММ.ГГГГ")
        return

    await state.update_data(date=date_obj)
    data = await state.get_data()

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Подтвердить", callback_data="confirm")],
            [types.InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ]
    )

    await message.answer(
        f"Проверьте данные:\nТип: {data['workout_type']}\n"
        f"Длительность: {data['duration']} мин\n"
        f"Дата: {message.text}",
        reply_markup=markup,
    )
    await state.set_state(WorkoutForm.confirm_data)


@workout_router.callback_query(F.data == "confirm", WorkoutForm.confirm_data)
async def save_workout(callback: types.CallbackQuery, state: FSMContext, pool: asyncpg.Pool):
    data = await state.get_data()

    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, username, full_name) VALUES ($1, $2, $3) "
                "ON CONFLICT (id) DO NOTHING",
                callback.from_user.id,
                callback.from_user.username,
                callback.from_user.full_name,
            )
            await conn.execute(
                "INSERT INTO workouts (user_id, type, duration, date) VALUES ($1, $2, $3, $4)",
                callback.from_user.id,
                data["workout_type"],
                data["duration"],
                data["date"],
            )
        await callback.message.answer("✅ Данные сохранены!", reply_markup=main_menu())

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка сохранения: {str(e)}")
        # logger.error(f"Database error: {str(e)}")

    await state.clear()


@workout_router.callback_query(F.data == "cancel")
@workout_router.message(Command("cancel"))
async def cancel_registration(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено", reply_markup=main_menu())
