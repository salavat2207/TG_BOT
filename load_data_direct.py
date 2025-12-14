"""Скрипт для прямой загрузки данных в БД на Render."""
import asyncio
import os
from setup_db import load_json_to_db
from dotenv import load_dotenv

load_dotenv()


async def main():
    """Загружает данные напрямую в БД."""
    print("=" * 50)
    print("Загрузка данных в базу данных")
    print("=" * 50)
    print()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ Ошибка: DATABASE_URL не установлен")
        print()
        print("Установите переменную окружения:")
        print("export DATABASE_URL='postgresql://user:password@host:port/database'")
        print()
        print("Или создайте .env файл с DATABASE_URL")
        return
    
    print(f"Подключение к базе данных...")
    print()
    
    try:
        await load_json_to_db()
        print()
        print("=" * 50)
        print("✅ Данные успешно загружены!")
        print("Бот готов к работе.")
        print("=" * 50)
    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ Ошибка: {e}")
        print("=" * 50)
        raise


if __name__ == "__main__":
    asyncio.run(main())
