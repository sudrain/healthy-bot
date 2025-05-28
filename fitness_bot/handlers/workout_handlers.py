import asyncpg
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

# from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
#    Общие функции
# -------------------------------


async def delete_previous_keyboard(callback: types.CallbackQuery):
    """Удаляет предыдущее сообщение с клавиатурой"""
    try:
        await callback.message.delete()
    except Exception:
        pass


async def format_exercise_data(data: dict) -> str:
    """Форматирует данные упражнения для отображения"""
    if data["workout_type"] == "cardio":
        return (
            "🏃 Кардио упражнение:\n"
            f"• Название: {data['exercise_name']}\n"
            f"• Длительность: {data.get('duration', 0)} мин\n"
            f"• Расстояние: {data.get('distance', 0)} км\n"
            f"• Скорость: {data.get('speed', 0)} км/ч\n"
            f"• Пульс: {data.get('heart_rate', 0)} уд/мин"
        )
    else:
        return (
            "🏋️ Силовое упражнение:\n"
            f"• Название: {data['exercise_name']}\n"
            f"• Повторения: {data.get('reps', 0)}\n"
            f"• Вес: {data.get('weight', 0)} кг\n"
            f"• Подходы: {data.get('sets', 0)}"
        )


# -------------------------------
#    Начало тренировки
# -------------------------------


@workout_router.callback_query(F.data == "add_workout")
async def start_workout(callback: types.CallbackQuery, state: FSMContext):
    await delete_previous_keyboard(callback)
    await callback.message.answer(
        "Выберите тип тренировки:", reply_markup=await keyboards.get_workout_type_kb()
    )
    await state.set_state(WorkoutForm.select_workout_type)
    await callback.answer()


# -------------------------------
#    Выбор типа тренировки
# -------------------------------


@workout_router.callback_query(WorkoutForm.select_workout_type, F.data.startswith("workout_type:"))
async def select_workout_type(callback: types.CallbackQuery, state: FSMContext, pool: asyncpg.Pool):
    workout_type = callback.data.split(":")[1]
    await state.update_data(workout_type=workout_type, exercises=[])

    await delete_previous_keyboard(callback)
    await callback.message.answer(
        "Выберите упражнение:", reply_markup=await keyboards.get_exercises_kb(pool, workout_type)
    )
    await state.set_state(WorkoutForm.select_exercise)
    await callback.answer()


# -------------------------------
#    Выбор упражнения
# -------------------------------


@workout_router.callback_query(WorkoutForm.select_exercise, F.data.startswith("exercise:"))
async def select_exercise(callback: types.CallbackQuery, state: FSMContext, pool: asyncpg.Pool):
    exercise_id = int(callback.data.split(":")[1])
    data = await state.get_data()

    # Получаем название упражнения
    async with pool.acquire() as conn:
        exercise_name = await conn.fetchval(
            "SELECT name FROM exercise_types WHERE id = $1", exercise_id
        )

    # Сохраняем текущее упражнение
    current_exercise = {"id": exercise_id, "name": exercise_name, "params": {}}
    await state.update_data(current_exercise=current_exercise, current_param=None, param_value=0)

    await delete_previous_keyboard(callback)

    # Определяем параметры для типа тренировки
    if data["workout_type"] == "cardio":
        param_name = "duration"
        text = "⏱ Установите продолжительность (мин):"
    else:
        param_name = "sets"
        text = "🔢 Установите количество подходов:"

    await state.update_data(current_param=param_name)
    await callback.message.answer(text, reply_markup=keyboards.get_number_input_kb(param_name))
    await state.set_state(WorkoutForm.enter_params)
    await callback.answer()


# -------------------------------
#    Ввод параметров
# -------------------------------


@workout_router.callback_query(WorkoutForm.enter_params, F.data.startswith("adjust:"))
async def adjust_parameter(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    _, param_name, delta = callback.data.split(":")
    delta = int(delta)

    # Обновляем значение
    new_value = max(0, data["param_value"] + delta)
    await state.update_data(param_value=new_value)

    # Редактируем сообщение с новым значением
    await callback.message.edit_reply_markup(
        reply_markup=keyboards.get_number_input_kb(param_name, new_value)
    )
    await callback.answer()


@workout_router.callback_query(WorkoutForm.enter_params, F.data.startswith("confirm_value:"))
async def confirm_parameter(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    param_name = callback.data.split(":")[1]
    param_value = data["param_value"]

    # Сохраняем параметр в текущем упражнении
    current_exercise = data["current_exercise"]
    current_exercise["params"][param_name] = param_value
    await state.update_data(current_exercise=current_exercise)

    # Определяем следующий параметр
    next_param = None
    if data["workout_type"] == "cardio":
        params_order = ["duration", "distance", "speed", "heart_rate"]
    else:
        params_order = ["sets", "reps", "weight"]

    current_index = params_order.index(param_name)
    if current_index < len(params_order) - 1:
        next_param = params_order[current_index + 1]

    await delete_previous_keyboard(callback)

    if next_param:
        # Переходим к следующему параметру
        await state.update_data(current_param=next_param, param_value=0)

        param_texts = {
            "duration": "⏱ Установите продолжительность (мин):",
            "distance": "📏 Установите расстояние (км):",
            "speed": "📈 Установите среднюю скорость (км/ч):",
            "heart_rate": "❤️ Установите средний пульс (уд/мин):",
            "sets": "🔢 Установите количество подходов:",
            "reps": "🔄 Установите количество повторений:",
            "weight": "🏋️ Установите вес (кг):",
        }

        await callback.message.answer(
            param_texts[next_param], reply_markup=keyboards.get_number_input_kb(next_param)
        )
    else:
        # Все параметры заполнены - подтверждение упражнения
        exercise_text = await format_exercise_data(
            {
                **current_exercise["params"],
                "exercise_name": current_exercise["name"],
                "workout_type": data["workout_type"],
            }
        )

        await callback.message.answer(
            f"Проверьте данные упражнения:\n\n{exercise_text}",
            reply_markup=keyboards.get_confirmation_kb(),
        )
        await state.set_state(WorkoutForm.confirm_exercise)

    await callback.answer()


# -------------------------------
#    Подтверждение упражнения
# -------------------------------


@workout_router.callback_query(WorkoutForm.confirm_exercise, F.data == "confirm_exercise")
async def confirm_exercise(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # Добавляем упражнение в список
    exercises = data["exercises"]
    exercises.append(data["current_exercise"])
    await state.update_data(exercises=exercises)

    await delete_previous_keyboard(callback)
    await callback.message.answer(
        "✅ Упражнение добавлено!", reply_markup=keyboards.get_add_another_kb()
    )
    await state.set_state(WorkoutForm.add_another)
    await callback.answer()


@workout_router.callback_query(WorkoutForm.confirm_exercise, F.data == "edit_exercise")
async def edit_exercise(callback: types.CallbackQuery, state: FSMContext, pool: asyncpg.Pool):
    data = await state.get_data()
    workout_type = data["workout_type"]

    await delete_previous_keyboard(callback)
    await callback.message.answer(
        "Выберите упражнение:", reply_markup=await keyboards.get_exercises_kb(pool, workout_type)
    )
    await state.set_state(WorkoutForm.select_exercise)
    await callback.answer()


# -------------------------------
#    Добавление/завершение
# -------------------------------


@workout_router.callback_query(WorkoutForm.add_another, F.data == "add_another")
async def add_another_exercise(
    callback: types.CallbackQuery, state: FSMContext, pool: asyncpg.Pool
):
    data = await state.get_data()

    await delete_previous_keyboard(callback)
    await callback.message.answer(
        "Выберите упражнение:",
        reply_markup=await keyboards.get_exercises_kb(pool, data["workout_type"]),
    )
    await state.set_state(WorkoutForm.select_exercise)
    await callback.answer()


@workout_router.callback_query(WorkoutForm.add_another, F.data == "finish_workout")
async def finish_workout(callback: types.CallbackQuery, state: FSMContext, pool: asyncpg.Pool):
    data = await state.get_data()
    user = callback.from_user

    try:
        async with pool.acquire() as conn:
            # Создаем/обновляем пользователя
            await create_user(conn, user)

            # Создаем тренировку
            workout_id = await create_workout(
                conn=conn, user_id=user.id, workout_type=data["workout_type"]
            )

            # Сохраняем все упражнения
            for exercise in data["exercises"]:
                params = exercise["params"]

                if data["workout_type"] == "cardio":
                    await create_cardio_session(
                        conn=conn,
                        workout_id=workout_id,
                        exercise_id=exercise["id"],
                        duration=params.get("duration", 0),
                        distance=params.get("distance", 0),
                        avg_speed=params.get("speed", 0),
                        heart_rate=params.get("heart_rate", 0),
                    )
                else:
                    await create_strength_session(
                        conn=conn,
                        workout_id=workout_id,
                        exercise_id=exercise["id"],
                        sets=params.get("sets", 0),
                        reps=params.get("reps", 0),
                        weight=params.get("weight", 0),
                    )

        await delete_previous_keyboard(callback)
        await callback.message.answer("✅ Тренировка успешно сохранена!")

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка сохранения: {str(e)}")

    finally:
        await state.clear()
        await callback.answer()


# -------------------------------
#    Обработка отмены
# -------------------------------


@workout_router.callback_query(F.data == "cancel")
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    await delete_previous_keyboard(callback)
    await callback.message.answer("❌ Действие отменено")
    await state.clear()
    await callback.answer()
