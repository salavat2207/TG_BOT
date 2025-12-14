from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
import asyncio


BOT_TOKEN = '8017260411:AAE4sLM31_E5bAtoJM_cgL-iw5l4uN9Tx7k'

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command('start'))
async def start_message(message: Message):
    await message.answer('Hello, world!')



if __name__ == '__main__':
    dp.run_polling(bot)

#