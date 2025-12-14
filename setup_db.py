import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import asyncpg
from dotenv import load_dotenv

load_dotenv()


def parse_database_url(database_url: str):
    """Парсит DATABASE_URL и возвращает параметры подключения."""
    if not database_url:
        raise ValueError("DATABASE_URL не установлен")
    
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
        "database": parsed.path.lstrip("/").split("?")[0],  
    }


async def init_database():
    """Выполняет миграции для создания таблиц."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL не установлен в переменных окружения")

    params = parse_database_url(database_url)
    
    print(f"Подключение к базе данных {params['database']}...")
    
    conn = await asyncpg.connect(
        user=params["user"],
        password=params["password"],
        database=params["database"],
        host=params["host"],
        port=params["port"],
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


async def load_json_to_db():
    """Загружает данные из videos.json в PostgreSQL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL не установлен в переменных окружения")

    params = parse_database_url(database_url)
    
    print(f"Подключение к базе данных {params['database']}...")
    
    conn = await asyncpg.connect(
        user=params["user"],
        password=params["password"],
        database=params["database"],
        host=params["host"],
        port=params["port"],
    )

    try:
        json_path = Path(__file__).parent / "app" / "videos.json"
        print(f"Загрузка данных из {json_path}...")

        if not json_path.exists():
            raise FileNotFoundError(f"Файл {json_path} не найден")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        videos = data.get("videos", [])
        print(f"Найдено видео: {len(videos)}")

        await conn.execute("TRUNCATE TABLE video_snapshots CASCADE")
        await conn.execute("TRUNCATE TABLE videos CASCADE")
        print("Все таблицы очищены")

        inserted_videos = 0
        inserted_snapshots = 0

        async with conn.transaction():
            for video in videos:
                video_created_at = datetime.fromisoformat(video["video_created_at"].replace("Z", "+00:00"))
                created_at = datetime.fromisoformat(video["created_at"].replace("Z", "+00:00"))
                updated_at = datetime.fromisoformat(video["updated_at"].replace("Z", "+00:00"))

                await conn.execute(
                    """
                    INSERT INTO videos (
                        id, creator_id, video_created_at, views_count,
                        likes_count, comments_count, reports_count,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    video["id"],
                    video["creator_id"],
                    video_created_at,
                    video["views_count"],
                    video["likes_count"],
                    video["comments_count"],
                    video["reports_count"],
                    created_at,
                    updated_at,
                )
                inserted_videos += 1

                for snapshot in video.get("snapshots", []):
                    snapshot_created_at = datetime.fromisoformat(snapshot["created_at"].replace("Z", "+00:00"))
                    snapshot_updated_at = datetime.fromisoformat(snapshot["updated_at"].replace("Z", "+00:00"))

                    await conn.execute(
                        """
                        INSERT INTO video_snapshots (
                            id, video_id, views_count, likes_count,
                            comments_count, reports_count,
                            delta_views_count, delta_likes_count,
                            delta_comments_count, delta_reports_count,
                            created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        snapshot["id"],
                        snapshot["video_id"],
                        snapshot["views_count"],
                        snapshot["likes_count"],
                        snapshot["comments_count"],
                        snapshot["reports_count"],
                        snapshot["delta_views_count"],
                        snapshot["delta_likes_count"],
                        snapshot["delta_comments_count"],
                        snapshot["delta_reports_count"],
                        snapshot_created_at,
                        snapshot_updated_at,
                    )
                    inserted_snapshots += 1

                if inserted_videos % 100 == 0:
                    print(f"Обработано видео: {inserted_videos}")

        print(f"\nЗагрузка завершена!")
        print(f"Вставлено видео: {inserted_videos}")
        print(f"Вставлено снапшотов: {inserted_snapshots}")

    finally:
        await conn.close()


async def main():
    """Главная функция: выполняет миграции и загружает данные."""
    print("=" * 50)
    print("Настройка базы данных")
    print("=" * 50)
    
    try:
        print("\n[1/2] Выполнение миграций...")
        await init_database()
        
        # Шаг 2: Загрузка данных
        print("\n[2/2] Загрузка данных из videos.json...")
        await load_json_to_db()
        
        print("\n" + "=" * 50)
        print("База данных успешно настроена!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
