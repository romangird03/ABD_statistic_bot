from aiogram import Router, types
from aiogram.filters import CommandStart

from app.keyboards.stats import stats_menu_keyboard

router = Router()


@router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "Привет! Я бот для статистики каналов.\n\n"
        "Команды:\n"
        "— /stats [YYYY-MM-DD] — сводная статистика по всем каналам\n"
        "Если дату не указать, беру актуальную (с лагом 2 дня).\n\n"
        "Можешь также пользоваться кнопками ниже.",
        reply_markup=stats_menu_keyboard(),
    )
