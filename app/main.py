import asyncio

from aiogram import Bot, Dispatcher

from app.config import load_config
from app.handlers import start as start_handlers
from app.handlers import stats as stats_handlers
from app.services.hse_client import HseApiClient


async def run_bot():
    config = load_config()

    bot = Bot(token=config.bot.token)
    dp = Dispatcher()

    api_client = HseApiClient(config)

    # регистрируем роутеры
    dp.include_router(start_handlers.router)
    stats_handlers.setup_stats_handlers(stats_handlers.router, api_client, config)
    dp.include_router(stats_handlers.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
