"""Модуль для обработки естественного языка и преобразования в SQL запросы."""
import os
import re

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()


class NLPHandler:
    """Класс для обработки естественного языка с помощью LLM."""

    def __init__(self):
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        if groq_api_key:
            self.client = AsyncOpenAI(
                api_key=groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self.model = "llama-3.3-70b-versatile"
            self.provider = "groq"
        else:
            raise ValueError(
                "Необходимо установить GROQ_API_KEY в .env файле.\n"
                "Получите бесплатный ключ на https://console.groq.com/"
            )

        self.system_prompt = """Ты - эксперт по SQL и анализу данных. Твоя задача - преобразовывать вопросы на русском языке в SQL запросы для PostgreSQL.

Схема базы данных:

1. Таблица videos (итоговая статистика по видео):
   - id (UUID) - идентификатор видео
   - creator_id (VARCHAR) - идентификатор креатора
   - video_created_at (TIMESTAMP) - дата и время публикации видео
   - views_count (INTEGER) - финальное количество просмотров
   - likes_count (INTEGER) - финальное количество лайков
   - comments_count (INTEGER) - финальное количество комментариев
   - reports_count (INTEGER) - финальное количество жалоб
   - created_at (TIMESTAMP) - служебное поле
   - updated_at (TIMESTAMP) - служебное поле

2. Таблица video_snapshots (почасовые замеры статистики):
   - id (VARCHAR) - идентификатор снапшота
   - video_id (UUID) - ссылка на видео (внешний ключ к videos.id)
   - views_count (INTEGER) - текущее количество просмотров на момент замера
   - likes_count (INTEGER) - текущее количество лайков на момент замера
   - comments_count (INTEGER) - текущее количество комментариев на момент замера
   - reports_count (INTEGER) - текущее количество жалоб на момент замера
   - delta_views_count (INTEGER) - приращение просмотров с прошлого замера
   - delta_likes_count (INTEGER) - приращение лайков с прошлого замера
   - delta_comments_count (INTEGER) - приращение комментариев с прошлого замера
   - delta_reports_count (INTEGER) - приращение жалоб с прошлого замера
   - created_at (TIMESTAMP) - время замера (раз в час)
   - updated_at (TIMESTAMP) - служебное поле

Важные правила:
- Всегда возвращай ТОЛЬКО SQL запрос, без дополнительных пояснений
- Запрос должен возвращать одно число (используй COUNT, SUM, или другую агрегатную функцию)
- Для работы с датами используй функции PostgreSQL: DATE(), TO_DATE(), DATE_TRUNC()
- Даты в формате "28 ноября 2025" преобразуй в DATE('2025-11-28')
- Диапазоны дат "с 1 по 5 ноября 2025" преобразуй в BETWEEN DATE('2025-11-01') AND DATE('2025-11-05')
- Для фильтрации по дате публикации видео используй video_created_at
- Для фильтрации по дате замера используй created_at в таблице video_snapshots
- Если вопрос про прирост/изменение, используй поля delta_* из video_snapshots
- Если вопрос про итоговые значения, используй таблицу videos
- Для подсчета уникальных видео используй COUNT(DISTINCT video_id) или COUNT(DISTINCT id)

Примеры преобразования:

Вопрос: "Сколько всего видео есть в системе?"
SQL: SELECT COUNT(*) FROM videos;

Вопрос: "Сколько видео у креатора с id abc123 вышло с 1 ноября 2025 по 5 ноября 2025 включительно?"
SQL: SELECT COUNT(*) FROM videos WHERE creator_id = 'abc123' AND video_created_at BETWEEN DATE('2025-11-01') AND DATE('2025-11-05');

Вопрос: "Сколько видео набрало больше 100000 просмотров за всё время?"
SQL: SELECT COUNT(*) FROM videos WHERE views_count > 100000;

Вопрос: "На сколько просмотров в сумме выросли все видео 28 ноября 2025?"
SQL: SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE DATE(created_at) = DATE('2025-11-28');

Вопрос: "Сколько разных видео получали новые просмотры 27 ноября 2025?"
SQL: SELECT COUNT(DISTINCT video_id) FROM video_snapshots WHERE DATE(created_at) = DATE('2025-11-27') AND delta_views_count > 0;

Теперь преобразуй следующий вопрос в SQL:"""

    async def text_to_sql(self, user_query: str) -> str:
        """
        Преобразует текстовый запрос на русском языке в SQL.

        Args:
            user_query: Вопрос пользователя на русском языке

        Returns:
            SQL запрос в виде строки
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_query},
                ],
                temperature=0.1,
                max_tokens=500,
            )

            sql_query = response.choices[0].message.content.strip()

            sql_query = re.sub(r"```sql\n?", "", sql_query)
            sql_query = re.sub(r"```\n?", "", sql_query)
            sql_query = sql_query.strip()

            if sql_query.endswith(";"):
                sql_query = sql_query[:-1]

            return sql_query

        except Exception as e:
            error_str = str(e)
            if "insufficient_quota" in error_str or "429" in error_str:
                raise ValueError(
                    "Превышен лимит запросов к Groq API. "
                    "Проверьте лимиты на https://console.groq.com/"
                )
            elif "invalid_api_key" in error_str or "401" in error_str or "authentication" in error_str.lower():
                raise ValueError(
                    "Неверный API ключ Groq. Проверьте:\n"
                    "1. Правильность ключа в .env файле (GROQ_API_KEY=...)\n"
                    "2. Что ключ скопирован полностью без пробелов\n"
                    "3. Получите новый ключ на https://console.groq.com/keys"
                )
            elif "model_decommissioned" in error_str or ("model" in error_str.lower() and "decommissioned" in error_str.lower()):
                raise ValueError(
                    "Модель Groq устарела. Код обновлен на актуальную модель. "
                    "Перезапустите бота. Если ошибка сохраняется, проверьте доступные модели на https://console.groq.com/docs/models"
                )
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Ошибка API ({self.provider}): {error_str}")
                raise ValueError(f"Ошибка при обработке запроса: {error_str}")
#