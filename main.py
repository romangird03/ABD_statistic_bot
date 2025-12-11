# app/main.py
import asyncio
import os
from datetime import date, timedelta

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import load_config
from app.handlers import start as start_handlers
from app.handlers import stats as stats_handlers
from app.handlers.stats import build_total_stats_text
from app.services.hse_client import HseApiClient


async def send_hourly_report(bot: Bot, api_client: HseApiClient, target_chat_id: int):
    """
    Отправляет общую статистику за (today - 2) в указанный чат.
    Эту функцию будет вызывать планировщик каждый час.
    """
    target_date = date.today() - timedelta(days=2)
    date_str = target_date.isoformat()

    try:
        data = await api_client.get_channel_stats(target_date)
    except Exception as e:
        # В проде это лучше логировать, но на первое время можно и так
        await bot.send_message(
            target_chat_id,
            f"❌ Ошибка при запросе API для часового отчёта: {e}",
        )
        return

    if not data:
        await bot.send_message(
            target_chat_id,
            f"Нет данных за {date_str} для часового отчёта.",
        )
        return

    text = build_total_stats_text(data, date_str)
    await bot.send_message(target_chat_id, text)


async def run_bot():
    config = load_config()

    bot = Bot(token=config.bot.token)
    dp = Dispatcher(storage=MemoryStorage())

    api_client = HseApiClient(config)

    # === Планировщик задач ===
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    report_chat_id_str = os.getenv("REPORT_CHAT_ID")
    if report_chat_id_str:
        report_chat_id = int(report_chat_id_str)

        # ОТЧЁТ КАЖДЫЙ ДЕНЬ В 7 УТРА
        scheduler.add_job(
            send_hourly_report,
            "cron",
            hour=7,
            minute=0,
            args=[bot, api_client, report_chat_id],
        )

        scheduler.start()
        print("Scheduler started. Daily report job scheduled.")
    else:
        print("REPORT_CHAT_ID is not set; scheduler job NOT scheduled.")

    # === Роутеры ===
    dp.include_router(start_handlers.router)
    stats_handlers.setup_stats_handlers(
        stats_handlers.router, api_client, config)
    dp.include_router(stats_handlers.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
