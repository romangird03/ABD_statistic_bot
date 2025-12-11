from datetime import date, timedelta

from aiogram import Router, types
from aiogram.filters import Command

from app.services.hse_client import HseApiClient
from app.config import Config

router = Router()


def fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def build_stats_text(data, date_str: str) -> str:
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
    return text


def setup_stats_handlers(router: Router, api_client: HseApiClient, config: Config):
    @router.message(Command("stats"))
    async def stats_handler(message: types.Message):
        parts = message.text.split()

        if len(parts) > 1:
            date_str = parts[1]
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                await message.answer(
                    "❌ Неверный формат даты. Используй YYYY-MM-DD, например: /stats 2025-12-07"
                )
                return
        else:
            target_date = date.today() - timedelta(days=2)
            date_str = target_date.isoformat()

        try:
            data = await api_client.get_channel_stats(target_date)
        except Exception as e:
            await message.answer(f"❌ Ошибка при запросе API: {e}")
            return

        if not data:
            await message.answer(f"Нет данных за {date_str}.")
            return

        text = build_stats_text(data, date_str)
        await message.answer(text)
