from aiogram.fsm.state import State, StatesGroup


class WorkoutForm(StatesGroup):
    select_workout_type = State()
    enter_duration = State()
    enter_date = State()
    confirm_data = State()
