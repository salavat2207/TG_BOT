import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

from bot.database import db
from bot.nlp_handler import NLPHandler

load_dotenv()

logger = logging.getLogger(__name__)

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот для аналитики по видео.\n\n"
        "Задай мне вопрос на русском языке, и я найду ответ в базе данных.\n\n"
        "Примеры вопросов:\n"
        "• Сколько всего видео есть в системе?\n"
        "• Сколько видео у креатора с id ... вышло с 1 ноября 2025 по 5 ноября 2025?\n"
        "• На сколько просмотров в сумме выросли все видео 28 ноября 2025?"
    )


@dp.message(F.text)
async def handle_text_message(message: Message):
    user_query = message.text.strip()

    if not user_query:
        await message.answer("Пожалуйста, задайте вопрос на русском языке.")
        return

    try:
        await message.answer("Обрабатываю запрос...")

        nlp_handler = NLPHandler()

        sql_query = await nlp_handler.text_to_sql(user_query)
        logger.info(f"SQL запрос: {sql_query}")

        result = await db.execute_query(sql_query)

        await message.answer(str(int(result)))

    except ValueError as e:
        logger.error(f"Ошибка обработки запроса: {e}")
        await message.answer(f"Ошибка: {str(e)}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
        await message.answer("Произошла ошибка при обработке запроса. Попробуйте переформулировать вопрос.")


async def main():
    """Главная функция для запуска бота."""
    await db.connect()
    logger.info("Подключение к базе данных установлено")

    try:
        # Очищаем webhook, если он был установлен (для избежания конфликтов)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook очищен, запускаем polling")
        
        await dp.start_polling(bot)
    finally:
        await db.disconnect()
        logger.info("Подключение к базе данных закрыто")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

#