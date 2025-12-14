import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def load_json_to_db():
    """Загружает данные из videos.json в PostgreSQL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL не установлен в .env файле")


    parts = database_url.replace("postgresql://", "").split("/")
    db_name = parts[1]
    auth_host = parts[0].split("@")
    user_pass = auth_host[0].split(":")
    host_port = auth_host[1].split(":")

    conn = await asyncpg.connect(
        user=user_pass[0],
        password=user_pass[1],
        database=db_name,
        host=host_port[0],
        port=int(host_port[1]) if len(host_port) > 1 else 5432,
    )

    try:
        json_path = Path(__file__).parent / "videos.json"
        print(f"Загрузка данных из {json_path}...")

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


if __name__ == "__main__":
    asyncio.run(load_json_to_db())

