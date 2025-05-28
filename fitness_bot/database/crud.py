import asyncpg
from aiogram.types import User


async def create_user(conn: asyncpg.Connection, tg_user: User) -> None:
    await conn.execute(
        """INSERT INTO users (id, username, full_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (id) DO UPDATE SET
            username = EXCLUDED.username,
            full_name = EXCLUDED.full_name,
            last_active = NOW()""",
        tg_user.id,
        tg_user.username,
        tg_user.full_name,
    )


async def create_workout(conn: asyncpg.Connection, user_id: int, workout_type: str) -> int:
    return await conn.fetchval(
        """INSERT INTO workouts (user_id, type, done_date)
        VALUES ($1, $2, NOW())
        RETURNING id""",
        user_id,
        workout_type,
    )


async def create_cardio_session(
    conn: asyncpg.Connection,
    workout_id: int,
    exercise_id: int,
    duration: int,
    distance: float,
    avg_speed: float,
    heart_rate: int,
) -> None:
    await conn.execute(
        """INSERT INTO cardio_sessions
        (workout_id, exercise_type_id, duration, distance,
         avg_speed, avg_heart_rate)
        VALUES ($1, $2, $3, $4, $5, $6)""",
        workout_id,
        exercise_id,
        duration,
        distance,
        avg_speed,
        heart_rate,
    )


async def create_strength_session(
    conn: asyncpg.Connection,
    workout_id: int,
    exercise_id: int,
    reps: int,
    weight: float,
) -> None:
    await conn.execute(
        """INSERT INTO strength_sessions
        (workout_id, exercise_type_id, reps, weight)
        VALUES ($1, $2, $3, $4)""",
        workout_id,
        exercise_id,
        reps,
        weight,
    )
