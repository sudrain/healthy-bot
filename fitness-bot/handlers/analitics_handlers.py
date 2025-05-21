import asyncpg
from aiogram import F, Router, types
from aiogram.filters import Command
from keyboards import main_menu

analytics_router = Router()


@analytics_router.callback_query(F.data == "history")
async def show_history(callback: types.CallbackQuery, pool: asyncpg.Pool):
    try:
        async with pool.acquire() as conn:
            records = await conn.fetch(
                """
                SELECT type, duration, date
                FROM workouts
                WHERE user_id = $1
                ORDER BY date DESC
                LIMIT 10
            """,
                callback.from_user.id,
            )

        if not records:
            await callback.message.answer("📭 История тренировок пуста")
            return

        response = ["📅 Последние 10 тренировок:\n"]
        for idx, record in enumerate(records, 1):
            response.append(
                f"{idx}. {record['date']:%d.%m.%Y}: {record['type']} ({record['duration']} мин)"
            )

        await callback.message.answer("\n".join(response), reply_markup=main_menu())

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка загрузки истории ({e})")
        # logger.error(f"History error: {str(e)}")


@analytics_router.message(Command("stats"))
async def get_stats(message: types.Message, pool: asyncpg.Pool):
    try:
        async with pool.acquire() as conn:
            total = await conn.fetchval(
                """
                SELECT SUM(duration) FROM workouts
                WHERE user_id = $1
            """,
                message.from_user.id,
            )

            types_stats = await conn.fetch(
                """
                SELECT type, COUNT(*) as count, SUM(duration) as total
                FROM workouts
                WHERE user_id = $1
                GROUP BY type
            """,
                message.from_user.id,
            )

        stats_text = [
            "📊 Ваша статистика:",
            f"Общее время: {total or 0} мин",
            "\nПо типам тренировок:",
        ]

        for stat in types_stats:
            stats_text.append(f"➤ {stat['type']}: {stat['count']} раз, {stat['total']} мин")

        await message.answer("\n".join(stats_text))

    except Exception as e:
        await message.answer(f"❌ Ошибка загрузки статистики ({e})")
        # logger.error(f"Stats error: {str(e)}")
