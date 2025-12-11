from aiogram.filters import Command
from aiogram import Router, types
from aiogram.filters import CommandStart

from app.keyboards.stats import main_menu_keyboard

router = Router()


@router.message(Command("chatid"))
async def chatid_handler(message: types.Message):
    await message.answer(f"chat_id: {message.chat.id}")


@router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "Привет! Я бот для получения статистики каналов.\n\n"
        "Команды:\n"
        "— /stats [YYYY-MM-DD] — общая статистика по всем каналам\n"
        "Если дату не указать, беру актуальную (с лагом 2 дня).\n\n"
        "Или пользуйся меню ниже.",
        reply_markup=main_menu_keyboard(),
    )
