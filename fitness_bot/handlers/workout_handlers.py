import asyncpg
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
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


# ----------------------------------------
#    Общий обработчик отдыха(переделать)
# ----------------------------------------
@workout_router.message(WorkoutForm.cardio_rest)
@workout_router.message(WorkoutForm.strength_rest)
async def process_rest_time(message: types.Message, state: FSMContext, pool: asyncpg.Pool):
    data = await state.get_data()
    await state.update_data(rest_time=int(message.text))

    # Получаем название упражнения из БД
    async with pool.acquire() as conn:
        exercise_name = await conn.fetchval(
            "SELECT name FROM exercise_types WHERE id = $1", data["exercise_id"]
        )

    await state.update_data(exercise_name=exercise_name)

    # Формируем клавиатуру подтверждения
    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")],
        ]
    )

    formatted_data = await format_workout_data(await state.get_data())
    await message.answer(formatted_data, reply_markup=confirm_keyboard)
    await state.set_state(WorkoutForm.confirm_data)


@workout_router.callback_query(WorkoutForm.confirm_data, F.data.in_(["confirm", "cancel"]))
async def handle_confirmation(callback: types.CallbackQuery, state: FSMContext, pool: asyncpg.Pool):
    try:
        if callback.data == "confirm":
            data = await state.get_data()

            async with pool.acquire() as conn:
                async with conn.transaction():  # Общая транзакция
                    # Создаем/обновляем пользователя
                    await create_user(conn, callback.from_user)

                    # Создаем тренировку
                    workout_id = await create_workout(
                        conn=conn, user_id=callback.from_user.id, workout_type=data["workout_type"]
                    )

                    # Сохраняем данные в соответствующую таблицу
                    if data["workout_type"] == "cardio":
                        await create_cardio_session(
                            conn=conn,
                            workout_id=workout_id,
                            exercise_id=data["exercise_id"],
                            duration=data["duration"],
                            distance=data["distance"],
                            avg_speed=data["avg_speed"],
                            heart_rate=data["avg_heart_rate"],
                            rest_time=data["rest_time"],  # Брать из data, а не message.text
                        )
                    else:
                        await create_strength_session(  # Исправлено на strength
                            conn=conn,
                            workout_id=workout_id,
                            exercise_id=data["exercise_id"],
                            reps=data["reps"],
                            weight=data["weight"],
                            rest_time=data["rest_time"],
                        )

            await callback.message.answer("✅ Данные успешно сохранены!")
        else:
            await callback.message.answer("❌ Тренировка отменена")

    except Exception as e:
        # logger.error(f"Ошибка сохранения: {str(e)}", exc_info=True)
        await callback.message.answer(f"⚠️ Произошла ошибка при сохранении. Попробуйте снова.({e})")

    finally:
        await state.clear()
        await callback.message.answer("Главное меню:", reply_markup=keyboards.main_menu())
        await callback.answer()


async def format_workout_data(data: dict) -> str:
    """Форматирование данных тренировки в читаемый текст"""
    if data["workout_type"] == "cardio":
        return (
            "📝 Проверьте данные кардио-тренировки:\n"
            f"🏃 Упражнение: {data['exercise_name']}\n"
            f"⏱ Продолжительность: {data['duration']} мин\n"
            f"📏 Расстояние: {data['distance']} км\n"
            f"📈 Средняя скорость: {data['avg_speed']} км/ч\n"
            f"❤️ Средний пульс: {data['avg_heart_rate']} уд/мин\n"
            f"⏳ Время отдыха: {data['rest_time']} мин"
        )
    else:
        return (
            "📝 Проверьте данные силовой тренировки:\n"
            f"🏋️ Упражнение: {data['exercise_name']}\n"
            f"🔢 Повторения: {data['reps']}\n"
            f"🏋️ Вес: {data['weight']} кг\n"
            f"⏳ Время отдыха: {data['rest_time']} мин"
        )
