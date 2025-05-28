from aiogram.fsm.state import State, StatesGroup


class WorkoutForm(StatesGroup):
    select_workout_type = State()

    # Общие состояния для упражнений
    select_exercise = State()
    exercise_params = State()  # Параметры упражнения
    confirm_exercise = State()  # Подтверждение одного упражнения
    add_another = State()  # Выбор: добавить еще или завершить
    rest = State()  # отдых между упражнениями
    enter_params = State()

    # Cardio
    cardio_duration = State()
    cardio_distance = State()
    cardio_avg_speed = State()
    cardio_heart_rate = State()

    # Strength
    strength_reps = State()
    strength_weight = State()
    strength_sets = State()
