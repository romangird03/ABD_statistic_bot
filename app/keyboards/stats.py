from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def stats_menu_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(
                text="📊 Актуальная статистика",
                callback_data="stats:current",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📅 Выбрать дату",
                callback_data="stats:choose_date",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
