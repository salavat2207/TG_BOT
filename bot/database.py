"""Модуль для работы с базой данных PostgreSQL."""
import os
from typing import Optional

import asyncpg
from dotenv import load_dotenv

load_dotenv()


class Database:
    """Класс для работы с базой данных."""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Создает пул подключений к базе данных."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL не установлен в .env файле")

        parts = database_url.replace("postgresql://", "").split("/")
        db_name = parts[1]
        auth_host = parts[0].split("@")
        user_pass = auth_host[0].split(":")
        host_port = auth_host[1].split(":")

        self.pool = await asyncpg.create_pool(
            user=user_pass[0],
            password=user_pass[1],
            database=db_name,
            host=host_port[0],
            port=int(host_port[1]) if len(host_port) > 1 else 5432,
            min_size=1,
            max_size=10,
        )

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
