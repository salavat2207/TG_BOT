"""Модуль для работы с базой данных PostgreSQL."""
import logging
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import asyncpg
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def parse_database_url(database_url: str):
    """Парсит DATABASE_URL и возвращает параметры подключения."""
    if not database_url:
        raise ValueError("DATABASE_URL не установлен")
    
    # Удаляем префикс postgresql:// или postgres://
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "http://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "http://", 1)
    
    parsed = urlparse(database_url)
    
    return {
        "user": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/").split("?")[0],  # Убираем параметры запроса
    }


class Database:
    """Класс для работы с базой данных."""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def check_tables_exist(self) -> bool:
        """Проверяет, существуют ли таблицы в БД."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'videos'
                );
            """)
            return bool(result)

    async def check_data_exists(self) -> bool:
        """Проверяет, есть ли данные в таблице videos."""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM videos")
            return count > 0

    async def init_tables_if_needed(self):
        """Инициализирует таблицы, если их нет."""
        try:
            tables_exist = await self.check_tables_exist()
            if tables_exist:
                logger.info("Таблицы уже существуют в базе данных")
                return

            logger.info("Таблицы не найдены, выполняется инициализация...")
            migration_file = Path(__file__).parent.parent / "migrations" / "001_create_tables.sql"
            
            if not migration_file.exists():
                logger.error(f"Файл миграции не найден: {migration_file}")
                logger.error(f"Текущая директория: {Path.cwd()}")
                logger.error(f"Директория скрипта: {Path(__file__).parent.parent}")
                raise FileNotFoundError(f"Файл миграции не найден: {migration_file}")

            logger.info(f"Чтение миграции из {migration_file}...")
            async with self.pool.acquire() as conn:
                with open(migration_file, "r", encoding="utf-8") as f:
                    sql = f.read()
                    logger.info("Выполнение SQL миграции...")
                    await conn.execute(sql)
            
            logger.info("Миграция выполнена успешно, таблицы созданы")
        except Exception as e:
            logger.error(f"Ошибка при инициализации таблиц: {e}", exc_info=True)
            raise

    async def connect(self):
        """Создает пул подключений к базе данных."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL не установлен в переменных окружения")

        params = parse_database_url(database_url)

        self.pool = await asyncpg.create_pool(
            user=params["user"],
            password=params["password"],
            database=params["database"],
            host=params["host"],
            port=params["port"],
            min_size=1,
            max_size=10,
        )
        
        # Автоматическая инициализация таблиц при подключении
        await self.init_tables_if_needed()

    async def disconnect(self):
        """Закрывает пул подключений."""
        if self.pool:
            await self.pool.close()

    async def execute_query(self, query: str) -> Optional[float]:
        """
        Выполняет SQL запрос и возвращает числовой результат.

        Args:
            query: SQL запрос, который должен вернуть одно число

        Returns:
            Числовой результат запроса или None
        """
        async with self.pool.acquire() as conn:
            try:
                result = await conn.fetchval(query)
                if result is None:
                    return 0.0
                return float(result)
            except Exception as e:
                raise ValueError(f"Ошибка выполнения запроса: {str(e)}")

    async def execute_migration(self, migration_file: str):
        """Выполняет SQL миграцию из файла."""
        async with self.pool.acquire() as conn:
            with open(migration_file, "r", encoding="utf-8") as f:
                sql = f.read()
                await conn.execute(sql)


db = Database()

#
