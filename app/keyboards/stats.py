from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# список каналов
CHANNELS = [
    "tass_agency",
    "markettwits",
    "rian_ru",
    "rbc_news",
    "banksta",
    "headlines_for_traders",
    "information_disclosure",
    "interfaxonline",
    "banki_economy",
    "economylive",
    "if_market_news",
    "cbrstocks",
    "ecotopor",
]


def main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(
                text="📊 Общая статистика",
                callback_data="stats:total",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📈 Статистика по паблику",
                callback_data="stats:by_channel",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def channels_keyboard() -> InlineKeyboardMarkup:
    rows = []
    # делаем по 2 канала в ряд
    for i in range(0, len(CHANNELS), 2):
        row = []
        for ch in CHANNELS[i: i + 2]:
            row.append(
                InlineKeyboardButton(
                    text=ch,
                    callback_data=f"channel:{ch}",
                )
            )
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def period_keyboard(channel: str) -> InlineKeyboardMarkup:
    """
    Кнопки выбора периода для конкретного канала.
    В callback_data зашиваем и период, и канал.
    """
    kb = [
        [
            InlineKeyboardButton(
                text="📅 За последний день",
                callback_data=f"period:day:{channel}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🗓 За последнюю неделю",
                callback_data=f"period:week:{channel}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📆 Пользовательский диапазон",
                callback_data=f"period:custom:{channel}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
