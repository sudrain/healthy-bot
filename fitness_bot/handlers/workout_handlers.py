import asyncpg
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from database.crud import (
    create_cardio_session,
    create_strength_session,
    create_user,
    create_workout,
)
from keyboards import keyboards
from states import WorkoutForm

workout_router = Router()


# -------------------------------
#    Общий обработчик отмены
# -------------------------------


async def cancel_operation(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Действие отменено. Возврат в главное меню.", reply_markup=ReplyKeyboardRemove()
    )
    await message.answer("Выберите действие:", reply_markup=keyboards.main_menu())


@workout_router.message(F.text.lower() == "❌ отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    await cancel_operation(message, state)


# -----------------------------------
#   Начало добавления тренировки
# -----------------------------------


@workout_router.message(F.text == "➕ Добавить тренировку")
async def start_workout(message: types.Message, state: FSMContext):
    await state.set_state(WorkoutForm.select_workout_type)
    markup = await keyboards.get_type_exercises()
    await message.answer("Выберите тип тренировки:", reply_markup=markup)


# -----------------------------------
#    Обработчики кардио-тренировки
# -----------------------------------
@workout_router.message(WorkoutForm.select_workout_type, F.text == "Кардио")
async def select_cardio_exercise(message: types.Message, state: FSMContext, pool: asyncpg.Pool):
    await state.update_data(workout_type="cardio")
    markup = await keyboards.get_cardio_exercises(pool)
    await message.answer("🏃 Выберите упражнение:", reply_markup=markup)
    await state.set_state(WorkoutForm.select_cardio_exercise)


@workout_router.message(WorkoutForm.select_cardio_exercise)
async def process_cardio_exercise(message: types.Message, state: FSMContext, pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        exercise = await conn.fetchrow(
            "SELECT id FROM exercise_types WHERE name = $1 AND category = 'cardio'", message.text
        )

    if not exercise:
        await message.answer("❌ Упражнение не найдено!")
        return

    await state.update_data(exercise_id=exercise["id"])
    await message.answer(
        "⏱ Введите продолжительность (минуты):", reply_markup=keyboards.cancel_button()
    )
    await state.set_state(WorkoutForm.cardio_duration)


@workout_router.message(WorkoutForm.cardio_duration)
async def process_cardio_duration(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите целое число минут!")
        return

    await state.update_data(duration=int(message.text))
    await message.answer("📏 Введите расстояние (км):", reply_markup=keyboards.cancel_button())
    await state.set_state(WorkoutForm.cardio_distance)


@workout_router.message(WorkoutForm.cardio_distance)
async def process_cardio_distance(message: types.Message, state: FSMContext):
    try:
        distance = float(message.text.replace(",", "."))
        if distance <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Некорректное значение! Пример: 5.3")
        return

    await state.update_data(distance=distance)
    await message.answer("📈 Введите среднюю скорость:", reply_markup=keyboards.speed_keyboard())
    await state.set_state(WorkoutForm.cardio_avg_speed)


@workout_router.message(WorkoutForm.cardio_avg_speed)
async def process_cardio_speed(message: types.Message, state: FSMContext):
    try:
        speed = float(message.text.replace(",", "."))
        if speed < 0 or speed > 30:  # Проверка на реалистичность
            raise ValueError
    except ValueError:
        await message.answer("❌ Некорректное значение! Пример: 9.5")
        return

    await state.update_data(avg_speed=speed)
    await message.answer("❤️ Введите средний пульс:", reply_markup=keyboards.cancel_button())
    await state.set_state(WorkoutForm.cardio_heart_rate)


@workout_router.message(WorkoutForm.cardio_heart_rate)
async def process_cardio_heart_rate(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число ударов в минуту!")
        return

    await state.update_data(avg_heart_rate=int(message.text))
    await message.answer(
        "⏳ Введите время отдыха после упражнения (минуты):", reply_markup=keyboards.cancel_button()
    )
    await state.set_state(WorkoutForm.cardio_rest)


@workout_router.message(WorkoutForm.cardio_rest)
async def process_cardio_rest(message: types.Message, state: FSMContext, pool: asyncpg.Pool):
    data = await state.get_data()

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Создаем/обновляем пользователя
            await create_user(conn, message.from_user)

            # Создаем тренировку
            workout_id = await create_workout(conn, message.from_user.id, "cardio")

            # Сохраняем кардио-сессию
            await create_cardio_session(
                conn,
                workout_id,
                data["exercise_id"],
                data["duration"],
                data["distance"],
                data["avg_speed"],
                data["avg_heart_rate"],
                int(message.text),
            )

    await message.answer("✅ Кардио-тренировка сохранена!")
    await state.clear()


# ------------------------------------
#    Обработчики силовой тренировки
# ------------------------------------


@workout_router.message(WorkoutForm.select_workout_type, F.text == "Силовая")
async def select_strength_exercise(message: types.Message, state: FSMContext, pool: asyncpg.Pool):
    await state.update_data(workout_type="strength")
    markup = await keyboards.get_strength_exercises(pool)
    await message.answer("🏋️ Выберите упражнение:", reply_markup=markup)
    await state.set_state(WorkoutForm.select_strength_exercise)


@workout_router.message(WorkoutForm.select_strength_exercise)
async def process_strength_exercise(message: types.Message, state: FSMContext, pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        exercise = await conn.fetchrow(
            "SELECT id FROM exercise_types WHERE name = $1 AND category = 'strength'", message.text
        )

    if not exercise:
        await message.answer("❌ Упражнение не найдено!")
        return

    await state.update_data(exercise_id=exercise["id"])
    await message.answer("Введите кол-во повторений:", reply_markup=keyboards.cancel_button())
    await state.set_state(WorkoutForm.strength_reps)


@workout_router.message(WorkoutForm.strength_reps)
async def process_strength_reps(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите целое число повторений!")
        return

    await state.update_data(reps=int(message.text))
    await message.answer("Введите вес (в кг):", reply_markup=keyboards.cancel_button())
    await state.set_state(WorkoutForm.strength_weight)


@workout_router.message(WorkoutForm.strength_weight)
async def process_strength_weight(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите вес в числовом значении!")
        return

    await state.update_data(weight=float(message.text))
    await message.answer(
        "⏳ Введите время отдыха после упражнения (минуты):", reply_markup=keyboards.cancel_button()
    )
    await state.set_state(WorkoutForm.strength_rest)


@workout_router.message(WorkoutForm.strength_rest)
async def process_strength_rest(message: types.Message, state: FSMContext, pool: asyncpg.Pool):
    data = await state.get_data()

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Создаем/обновляем пользователя
            await create_user(conn, message.from_user)

            # Создаем тренировку
            workout_id = await create_workout(conn, message.from_user.id, "strength")

            # Сохраняем силовую сессию
            await create_strength_session(
                conn,
                workout_id,
                data["exercise_id"],
                data["reps"],
                data["weight"],
                int(message.text),
            )

    await message.answer("✅ Силовая-тренировка сохранена!")
    await state.clear()
