from aiogram.fsm.state import State, StatesGroup


class WorkoutForm(StatesGroup):
    select_workout_type = State()

    # Cardio
    select_cardio_exercise = State()
    cardio_duration = State()
    cardio_distance = State()
    cardio_avg_speed = State()
    cardio_heart_rate = State()

    # Strength
    select_strength_exercise = State()
    strength_reps = State()
    strength_weight = State()

    confirm_data = State()
