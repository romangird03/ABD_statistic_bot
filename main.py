import asyncio
import os
import ssl
from datetime import date, timedelta

import aiohttp
import certifi
from aiohttp import BasicAuth
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv


# ==== ЗАГРУЖАЕМ .env ====
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_USER = os.getenv("API_USER")
API_PASS = os.getenv("API_PASS")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing in .env")
if not API_USER or not API_PASS:
    raise ValueError("API_USER или API_PASS отсутствуют в .env")

# ==== КОНСТАНТЫ ====
STATS_API_URL = "https://api.hse.panfilov.app/channel-stats"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def fmt_int(n: int) -> str:
    """1000000 -> '1 000 000'."""
    return f"{n:,}".replace(",", " ")


# ====== HANDLERS ======

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "Привет! Я бот для статистики каналов.\n\n"
        "Команды:\n"
        "/stats [YYYY-MM-DD] — сводная статистика по всем каналам.\n"
        "Если дату не указать, беру актуальную (с лагом 2 дня)."
    )


@dp.message(Command("stats"))
async def stats_handler(message: types.Message):
    parts = message.text.split()

    # /stats 2025-11-27  -> берём дату из команды
    if len(parts) > 1:
        date_str = parts[1]
    else:
        # данные в API за today-2, значит «актуальная» дата:
        target_date = date.today() - timedelta(days=2)
        date_str = target_date.isoformat()

    # Basic Auth для FastAPI
    auth = BasicAuth(API_USER, API_PASS)

    # SSL-контекст с certifi (нормальная проверка сертификатов)
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # ---- запрос к API ----
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                STATS_API_URL,
                params={"date": date_str},
                auth=auth,
                ssl=ssl_context,
            ) as resp:

                if resp.status == 401:
                    await message.answer("❌ API: неверный логин/пароль (401 Unauthorized).")
                    return

                if resp.status == 403:
                    await message.answer("❌ API: доступ запрещён (403 Forbidden).")
                    return

                if resp.status != 200:
                    await message.answer(f"❌ API вернуло статус {resp.status}.")
                    return

                data = await resp.json()

    except Exception as e:
        await message.answer(f"❌ Ошибка при запросе API: {e}")
        return

    if not data:
        await message.answer(f"Нет данных за {date_str}.")
        return

    # ---- агрегируем по всем каналам ----
    total_channels = len(data)
    total_posts = sum(ch["total_posts"] for ch in data)
    total_views = sum(ch["total_views"] for ch in data)
    total_forwards = sum(ch["total_forwards"] for ch in data)

    avg_views_per_post = int(total_views / total_posts) if total_posts else 0
    avg_forwards_per_post = total_forwards / total_posts if total_posts else 0.0

    top_by_views = max(data, key=lambda ch: ch["total_views"])

    text = (
        f"📊 Статистика каналов за {date_str}\n\n"
        f"Каналов: {total_channels}\n"
        f"Всего постов: {fmt_int(total_posts)}\n"
        f"Всего просмотров: {fmt_int(total_views)}\n"
        f"Всего пересылок: {fmt_int(total_forwards)}\n"
        f"Средние просмотры на пост: {fmt_int(avg_views_per_post)}\n"
        f"Средние пересылки на пост: {avg_forwards_per_post:.2f}\n\n"
        f"🔝 Топ по просмотрам:\n"
        f"• {top_by_views['channel_name']} — {fmt_int(top_by_views['total_views'])} просмотров"
    )

    await message.answer(text)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
