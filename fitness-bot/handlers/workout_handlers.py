import logging
from datetime import datetime

import asyncpg
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import WorkoutForm

logger = logging.getLogger(__name__)

workout_router = Router()


@workout_router.message(Command("add_workout"))
async def start_workout_registration(message: types.Message, state: FSMContext):
    await message.answer(
        "Выберите тип тренировки:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Силовая")],
                [types.KeyboardButton(text="Кардио")],
            ],
            resize_keyboard=True,
        ),
    )
    await state.set_state(WorkoutForm.select_workout_type)


# Обработка типа тренировки
@workout_router.message(WorkoutForm.select_workout_type)
async def process_workout_type(message: types.Message, state: FSMContext):
    await state.update_data(workout_type=message.text)
    await message.answer(
        "Введите продолжительность(в минутах):", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(WorkoutForm.enter_duration)


# Обработка продолжительности
@workout_router.message(WorkoutForm.enter_duration)
async def procces_duration(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите число!")
        return

    await state.update_data(duration=int(message.text))
    await message.answer("Введите дату тренировки (ДД.ММ.ГГГГ):")
    await state.set_state(WorkoutForm.enter_date)


# Обработка Даты и подтверждение
@workout_router.message(WorkoutForm.enter_date)
async def process_date(message: types.Message, state: FSMContext):
    try:
        # Преобразуем строку в объект date
        date_obj = datetime.strptime(message.text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("❌ Неверный формат даты! Используйте ДД.ММ.ГГГГ")
        return

    await state.update_data(date=date_obj)  # Сохраняем объект date, а не строку
    data = await state.get_data()
    await message.answer(
        f"Проверьте данные:\n"
        f"Тип: {data['workout_type']}\n"
        f"Длительность: {data['duration']} мин\n"
        f"Дата: {message.text}",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="Подтвердить", callback_data="confirm")],
                [types.InlineKeyboardButton(text="Отмена", callback_data="cancel")],
            ]
        ),
    )
    await state.set_state(WorkoutForm.confirm_data)


# Сохранение данных
@workout_router.callback_query(F.data == "confirm", WorkoutForm.confirm_data)
async def save_workout(
    callback: types.CallbackQuery,
    state: FSMContext,
    pool: asyncpg.Pool,  # Получаем pool из контекста
):
    data = await state.get_data()

    try:
        async with pool.acquire() as conn:  # Получаем соединение из пула
            async with conn.transaction():  # Явное начало транзакции
                # Сохраняем пользователя
                await conn.execute(
                    """
                    INSERT INTO users (id, username, full_name)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (id) DO NOTHING
                """,
                    callback.from_user.id,
                    callback.from_user.username,
                    callback.from_user.full_name,
                )

                # Сохраняем тренировку
                await conn.execute(
                    """
                    INSERT INTO workouts (user_id, type, duration, date)
                    VALUES ($1, $2, $3, $4)
                """,
                    callback.from_user.id,
                    data["workout_type"],
                    data["duration"],
                    data["date"],
                )

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка сохранения: {str(e)}")
        logger.error(f"Database error: {str(e)}")
    else:
        await callback.message.answer("✅ Данные успешно сохранены!")
    finally:
        await state.clear()


@workout_router.callback_query(F.data == "cancel", WorkoutForm.confirm_data)
async def cancel_registration(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("❌ Ввод прерван")
    await state.clear()


# @workout_router.message(Command("progress"))
# async def command_progress(message: types.Message) -> None:
#     await message.answer("progress")
