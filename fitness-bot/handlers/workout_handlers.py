from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import WorkoutForm

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
    """
    Тут нужно добавить валидацию даты либо добавить автодату в sql
    """
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
    await state.update_data(date=message.text)
    await state.set_state(WorkoutForm.confirm_data)


# Сохранение данных
@workout_router.callback_query(F.data == "confirm", WorkoutForm.confirm_data)
async def save_workout(callback: types.CallbackQuery, state: FSMContext):
    # Добавим БД позже
    # data = await state.get_data()
    await callback.message.answer("✅ Данные сохранены!")
    await state.clear()


@workout_router.callback_query(F.data == "cancel", WorkoutForm.confirm_data)
async def cancel_registration(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("❌ Ввод прерван")
    await state.clear()


# @workout_router.message(Command("progress"))
# async def command_progress(message: types.Message) -> None:
#     await message.answer("progress")
