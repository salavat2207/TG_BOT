import asyncio
import logging
import os
from aiohttp import web

from bot.bot import main as bot_main
from setup_db import load_json_to_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def health_check(request):
    """Health check endpoint для Render Web Service."""
    return web.json_response({"status": "ok", "service": "telegram-bot"})


async def load_data_endpoint(request):
    """Endpoint для загрузки данных в БД (только для инициализации)."""
    try:
        logger.info("Начало загрузки данных через HTTP endpoint...")
        await load_json_to_db()
        logger.info("Данные загружены успешно")
        return web.json_response({
            "status": "success", 
            "message": "Данные загружены успешно. Бот готов к работе!"
        })
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}", exc_info=True)
        return web.json_response(
            {"status": "error", "message": str(e)},
            status=500
        )


async def init_bot(app):
    """Инициализация бота в фоне."""
    logger.info("Запуск Telegram бота в фоне...")
    # Запускаем бота в фоне
    asyncio.create_task(bot_main())


async def cleanup_bot(app):
    """Очистка при остановке."""
    logger.info("Остановка сервиса...")


def create_app():
    """Создание приложения aiohttp."""
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    # Endpoint для загрузки данных (GET и POST для удобства)
    app.router.add_get("/load-data", load_data_endpoint)
    app.router.add_post("/load-data", load_data_endpoint)
    
    app.on_startup.append(init_bot)
    app.on_cleanup.append(cleanup_bot)
    
    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app = create_app()
    
    logger.info(f"Запуск HTTP сервера на порту {port}...")
    web.run_app(app, port=port, host="0.0.0.0")

