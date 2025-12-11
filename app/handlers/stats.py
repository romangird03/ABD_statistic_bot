from datetime import date, timedelta, datetime

from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.services.hse_client import HseApiClient
from app.config import Config
from app.keyboards.stats import (
    channels_keyboard,
    period_keyboard,
    main_menu_keyboard,
)

router = Router()


class StatsRange(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_end_date = State()


def fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def build_total_stats_text(data, date_label: str) -> str:
    total_channels = len(data)
    total_posts = sum(ch["total_posts"] for ch in data)
    total_views = sum(ch["total_views"] for ch in data)
    total_forwards = sum(ch["total_forwards"] for ch in data)

    avg_views_per_post = int(total_views / total_posts) if total_posts else 0
    avg_forwards_per_post = total_forwards / total_posts if total_posts else 0.0

    top_by_views = max(data, key=lambda ch: ch["total_views"])

    text = (
        f"📊 Общая статистика каналов за {date_label}\n\n"
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


def build_channel_stats_text(
    channel_name: str,
    total_posts: int,
    total_views: int,
    total_forwards: int,
    date_label: str,
) -> str:
    avg_views_per_post = int(total_views / total_posts) if total_posts else 0
    avg_forwards_per_post = total_forwards / total_posts if total_posts else 0.0

    text = (
        f"📈 Статистика канала <b>{channel_name}</b>\n"
        f"за период {date_label}\n\n"
        f"Постов: {fmt_int(total_posts)}\n"
        f"Просмотров всего: {fmt_int(total_views)}\n"
        f"Пересылок всего: {fmt_int(total_forwards)}\n"
        f"Средние просмотры на пост: {fmt_int(avg_views_per_post)}\n"
        f"Средние пересылки на пост: {avg_forwards_per_post:.2f}"
    )
    return text


def setup_stats_handlers(router: Router, api_client: HseApiClient, config: Config):
    # ===== /stats (общая статистика по дате) =====
    @router.message(Command("stats"))
    async def stats_command_handler(message: types.Message):
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

        text = build_total_stats_text(data, date_str)
        await message.answer(text, reply_markup=main_menu_keyboard())

    # ===== Кнопка "Общая статистика" =====
    @router.callback_query(F.data == "stats:total")
    async def stats_total_callback(callback: types.CallbackQuery):
        target_date = date.today() - timedelta(days=2)
        date_str = target_date.isoformat()

        try:
            data = await api_client.get_channel_stats(target_date)
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Ошибка при запросе API: {e}"
            )
            await callback.answer()
            return

        if not data:
            await callback.message.edit_text(f"Нет данных за {date_str}.")
            await callback.answer()
            return

        text = build_total_stats_text(data, date_str)

        try:
            await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
        except TelegramBadRequest as e:
            # Телеграм говорит "message is not modified" — просто игнорируем
            if "message is not modified" in str(e):
                await callback.answer(
                    "Уже показываю актуальную статистику 👍", show_alert=False
                )
                return
            # любая другая ошибка — пусть падает
            raise

        await callback.answer()

    # ===== Кнопка "Статистика по паблику" =====
    @router.callback_query(F.data == "stats:by_channel")
    async def stats_by_channel_callback(callback: types.CallbackQuery):
        await callback.message.edit_text(
            "Выбери канал:", reply_markup=channels_keyboard()
        )
        await callback.answer()

    # ===== Выбор канала =====
    @router.callback_query(F.data.startswith("channel:"))
    async def channel_chosen_callback(callback: types.CallbackQuery):
        _, channel = callback.data.split(":", 1)
        await callback.message.edit_text(
            f"Канал: <b>{channel}</b>\nВыбери период:",
            reply_markup=period_keyboard(channel),
            parse_mode="HTML",
        )
        await callback.answer()

    # ===== Период: последний день =====
    @router.callback_query(F.data.startswith("period:day:"))
    async def period_day_callback(callback: types.CallbackQuery):
        _, _, channel = callback.data.split(":", 2)
        target_date = date.today() - timedelta(days=2)
        date_str = target_date.isoformat()

        try:
            data = await api_client.get_channel_stats(target_date)
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка при запросе API: {e}")
            await callback.answer()
            return

        ch_data = next(
            (item for item in data if item["channel_name"] == channel),
            None,
        )

        if not ch_data:
            await callback.message.edit_text(
                f"Нет данных для канала {channel} за {date_str}."
            )
            await callback.answer()
            return

        text = build_channel_stats_text(
            channel_name=channel,
            total_posts=ch_data["total_posts"],
            total_views=ch_data["total_views"],
            total_forwards=ch_data["total_forwards"],
            date_label=date_str,
        )
        await callback.message.edit_text(text, parse_mode="HTML")
        await callback.answer()

    # ===== Период: последняя неделя =====
    @router.callback_query(F.data.startswith("period:week:"))
    async def period_week_callback(callback: types.CallbackQuery):
        _, _, channel = callback.data.split(":", 2)
        end_date = date.today() - timedelta(days=2)
        start_date = end_date - timedelta(days=6)  # 7 дней всего

        total_posts = 0
        total_views = 0
        total_forwards = 0

        cur_date = start_date
        try:
            while cur_date <= end_date:
                day_data = await api_client.get_channel_stats(cur_date)
                ch_data = next(
                    (item for item in day_data if item["channel_name"] == channel),
                    None,
                )
                if ch_data:
                    total_posts += ch_data["total_posts"]
                    total_views += ch_data["total_views"]
                    total_forwards += ch_data["total_forwards"]
                cur_date += timedelta(days=1)
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка при запросе API: {e}")
            await callback.answer()
            return

        if total_posts == 0:
            await callback.message.edit_text(
                f"Нет данных для канала {channel} за период "
                f"{start_date.isoformat()} — {end_date.isoformat()}."
            )
            await callback.answer()
            return

        date_label = f"{start_date.isoformat()} — {end_date.isoformat()}"
        text = build_channel_stats_text(
            channel_name=channel,
            total_posts=total_posts,
            total_views=total_views,
            total_forwards=total_forwards,
            date_label=date_label,
        )
        await callback.message.edit_text(text, parse_mode="HTML")
        await callback.answer()

    # ===== Период: пользовательский диапазон (кнопка) =====
    @router.callback_query(F.data.startswith("period:custom:"))
    async def period_custom_callback(callback: types.CallbackQuery, state: FSMContext):
        _, _, channel = callback.data.split(":", 2)

        # сохраняем выбранный канал в FSM, дальше будем его использовать
        await state.update_data(channel=channel)

        await callback.message.edit_text(
            f"Канал: <b>{channel}</b>\n"
            f"Введи начальную дату диапазона в формате YYYY-MM-DD",
            parse_mode="HTML",
        )
        await state.set_state(StatsRange.waiting_for_start_date)
        await callback.answer()

    # ===== Приём начальной даты =====
    @router.message(StateFilter(StatsRange.waiting_for_start_date))
    async def range_start_date_handler(message: types.Message, state: FSMContext):
        text = message.text.strip()

        try:
            start_date = datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            await message.answer(
                "❌ Неверный формат. Введи дату в формате YYYY-MM-DD, например: 2025-12-07"
            )
            return

        await state.update_data(start_date=start_date)

        await message.answer(
            "Теперь введи конечную дату диапазона в формате YYYY-MM-DD"
        )
        await state.set_state(StatsRange.waiting_for_end_date)

    # ===== Приём конечной даты + запрос статистики =====
    @router.message(StateFilter(StatsRange.waiting_for_end_date))
    async def range_end_date_handler(message: types.Message, state: FSMContext):
        text = message.text.strip()

        try:
            end_date = datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            await message.answer(
                "❌ Неверный формат. Введи дату в формате YYYY-MM-DD, например: 2025-12-14"
            )
            return

        data_state = await state.get_data()
        start_date = data_state.get("start_date")
        channel = data_state.get("channel")

        if start_date is None or channel is None:
            await message.answer(
                "Что-то пошло не так, начальная дата или канал потерялись. "
                "Начни заново через меню."
            )
            await state.clear()
            return

        if end_date < start_date:
            await message.answer(
                "❌ Конечная дата раньше начальной. Введи корректный диапазон."
            )
            return

        total_posts = 0
        total_views = 0
        total_forwards = 0

        cur_date = start_date
        try:
            while cur_date <= end_date:
                day_data = await api_client.get_channel_stats(cur_date)
                ch_data = next(
                    (item for item in day_data if item["channel_name"] == channel),
                    None,
                )
                if ch_data:
                    total_posts += ch_data["total_posts"]
                    total_views += ch_data["total_views"]
                    total_forwards += ch_data["total_forwards"]
                cur_date += timedelta(days=1)
        except Exception as e:
            await message.answer(f"❌ Ошибка при запросе API: {e}")
            await state.clear()
            return

        if total_posts == 0:
            await message.answer(
                f"Нет данных для канала {channel} за период "
                f"{start_date.isoformat()} — {end_date.isoformat()}."
            )
            await state.clear()
            return

        date_label = f"{start_date.isoformat()} — {end_date.isoformat()}"
        text = build_channel_stats_text(
            channel_name=channel,
            total_posts=total_posts,
            total_views=total_views,
            total_forwards=total_forwards,
            date_label=date_label,
        )
        await message.answer(text, parse_mode="HTML")
        await state.clear()
