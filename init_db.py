"""Скрипт для инициализации базы данных (выполнение миграций)."""
import asyncio
import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def init_database():
    """Выполняет миграции для создания таблиц."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL не установлен в .env файле")

    parts = database_url.replace("postgresql://", "").split("/")
    db_name = parts[1]
    auth_host = parts[0].split("@")
    user_pass = auth_host[0].split(":")
    host_port = auth_host[1].split(":")

    admin_conn = await asyncpg.connect(
        user=user_pass[0],
        password=user_pass[1],
        database="postgres", 
        host=host_port[0],
        port=int(host_port[1]) if len(host_port) > 1 else 5432,
    )

    try:
        db_exists = await admin_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )

        if not db_exists:
            print(f"Создание базы данных {db_name}...")
            await admin_conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"База данных {db_name} создана успешно!")
        else:
            print(f"База данных {db_name} уже существует.")
    finally:
        await admin_conn.close()

    conn = await asyncpg.connect(
        user=user_pass[0],
        password=user_pass[1],
        database=db_name,
        host=host_port[0],
        port=int(host_port[1]) if len(host_port) > 1 else 5432,
    )

    try:
        migration_file = Path(__file__).parent / "migrations" / "001_create_tables.sql"
        print(f"Выполнение миграции из {migration_file}...")

        with open(migration_file, "r", encoding="utf-8") as f:
            sql = f.read()
            await conn.execute(sql)

        print("Миграция выполнена успешно!")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(init_database())

