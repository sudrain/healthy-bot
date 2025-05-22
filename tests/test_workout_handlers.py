from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove

# from fitness_bot.database.crud import create_user, create_workout
from handlers.workout_handlers import workout_router
from states import WorkoutForm


@pytest.fixture
def memory_storage():
    return MemoryStorage()


@pytest.fixture
def bot():
    return AsyncMock()


@pytest.fixture
def pool():
    return AsyncMock()


@pytest.mark.asyncio
async def test_start_workout_command(bot, memory_storage):
    message = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=1, type="private"),
        text="➕ Добавить тренировку",
    )
    state = FSMContext(storage=memory_storage, key="test")

    await workout_router.message(message=message, state=state, bot=bot)

    current_state = await state.get_state()
    assert current_state == WorkoutForm.select_workout_type.state
    bot.send_message.assert_called_with(
        chat_id=1, text="Выберите тип тренировки:", reply_markup=AsyncMock()
    )


@pytest.mark.asyncio
async def test_cardio_flow(pool, bot, memory_storage):
    # Шаг 1: Выбор кардио
    message = types.Message(
        message_id=2, date=datetime.now(), chat=types.Chat(id=1, type="private"), text="Кардио"
    )
    state = FSMContext(storage=memory_storage, key="test")
    await state.set_state(WorkoutForm.select_workout_type)

    await workout_router.message(message=message, state=state, bot=bot, pool=pool)
    assert await state.get_state() == WorkoutForm.select_cardio_exercise.state

    # Шаг 2: Выбор упражнения
    message.text = "Бег"
    pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {"id": 1}
    await workout_router.message(message=message, state=state, bot=bot, pool=pool)
    assert await state.get_state() == WorkoutForm.cardio_duration.state

    # Шаг 3: Ввод продолжительности
    message.text = "30"
    await workout_router.message(message=message, state=state, bot=bot)
    data = await state.get_data()
    assert data["duration"] == 30
    assert await state.get_state() == WorkoutForm.cardio_distance.state

    # Шаг 4: Ввод расстояния
    message.text = "5.5"
    await workout_router.message(message=message, state=state, bot=bot)
    data = await state.get_data()
    assert data["distance"] == 5.5
    assert await state.get_state() == WorkoutForm.cardio_avg_speed.state

    # Шаг 5: Ввод скорости
    message.text = "10.5"
    await workout_router.message(message=message, state=state, bot=bot)
    data = await state.get_data()
    assert data["avg_speed"] == 10.5
    assert await state.get_state() == WorkoutForm.cardio_heart_rate.state

    # Шаг 6: Ввод пульса
    message.text = "120"
    await workout_router.message(message=message, state=state, bot=bot)
    data = await state.get_data()
    assert data["avg_heart_rate"] == 120
    assert await state.get_state() == WorkoutForm.cardio_rest.state

    # Шаг 7: Сохранение данных
    message.text = "2"
    with (
        patch("database.crud.create_user") as mock_create_user,
        patch("database.crud.create_workout") as mock_create_workout,
        patch("database.crud.create_cardio_session") as mock_create_cardio,
    ):
        mock_create_workout.return_value = 1
        await workout_router.message(message=message, state=state, bot=bot, pool=pool)

        mock_create_user.assert_awaited_once()
        mock_create_workout.assert_awaited_once()
        mock_create_cardio.assert_awaited_once()
        assert await state.get_state() is None


@pytest.mark.asyncio
async def test_invalid_input_handling(bot, memory_storage):
    # Тест неверного ввода продолжительности
    message = types.Message(
        message_id=3, date=datetime.now(), chat=types.Chat(id=1, type="private"), text="abc"
    )
    state = FSMContext(storage=memory_storage, key="test")
    await state.set_state(WorkoutForm.cardio_duration)

    await workout_router.message(message=message, state=state, bot=bot)

    bot.send_message.assert_called_with(
        chat_id=1, text="❌ Введите целое число минут!", reply_markup=AsyncMock()
    )
    assert await state.get_state() == WorkoutForm.cardio_duration.state


@pytest.mark.asyncio
async def test_cancel_handler(bot, memory_storage):
    message = types.Message(
        message_id=4, date=datetime.now(), chat=types.Chat(id=1, type="private"), text="❌ Отмена"
    )
    state = FSMContext(storage=memory_storage, key="test")
    await state.set_state(WorkoutForm.cardio_duration)

    await workout_router.message(message=message, state=state, bot=bot)

    assert await state.get_state() is None
    bot.send_message.assert_called_with(
        chat_id=1,
        text="❌ Действие отменено. Возврат в главное меню.",
        reply_markup=ReplyKeyboardRemove(),
    )


@pytest.mark.asyncio
async def test_strength_flow(pool, bot, memory_storage):
    # Шаг 1: Выбор силовой тренировки
    message = types.Message(
        message_id=5, date=datetime.now(), chat=types.Chat(id=1, type="private"), text="Силовая"
    )
    state = FSMContext(storage=memory_storage, key="test")
    await state.set_state(WorkoutForm.select_workout_type)

    await workout_router.message(message=message, state=state, bot=bot, pool=pool)
    assert await state.get_state() == WorkoutForm.select_strength_exercise.state

    # Шаг 2: Выбор упражнения
    message.text = "Приседания"
    pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {"id": 2}
    await workout_router.message(message=message, state=state, bot=bot, pool=pool)
    assert await state.get_state() == WorkoutForm.strength_reps.state

    # Шаг 3: Ввод повторений
    message.text = "10"
    await workout_router.message(message=message, state=state, bot=bot)
    data = await state.get_data()
    assert data["reps"] == 10
    assert await state.get_state() == WorkoutForm.strength_weight.state

    # Шаг 4: Ввод веса
    message.text = "80.5"
    await workout_router.message(message=message, state=state, bot=bot)
    data = await state.get_data()
    assert data["weight"] == 80.5
    assert await state.get_state() == WorkoutForm.strength_rest.state

    # Шаг 5: Сохранение данных
    message.text = "3"
    with (
        patch("database.crud.create_user") as mock_create_user,
        patch("database.crud.create_workout") as mock_create_workout,
        patch("database.crud.create_strength_session") as mock_create_strength,
    ):
        mock_create_workout.return_value = 2
        await workout_router.message(message=message, state=state, bot=bot, pool=pool)

        mock_create_user.assert_awaited_once()
        mock_create_workout.assert_awaited_once()
        mock_create_strength.assert_awaited_once()
        assert await state.get_state() is None
