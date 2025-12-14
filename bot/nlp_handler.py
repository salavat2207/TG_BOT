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
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Приоритет: Groq (бесплатный), затем OpenAI
        if groq_api_key:
            self.client = AsyncOpenAI(
                api_key=groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            # Список моделей для переключения при ошибках (актуальные модели Groq)
            # Проверенные модели: https://console.groq.com/docs/models
            self.groq_models = [
                "llama-3.1-70b-versatile",      # Основная модель (70B, 128k context)
                "llama-3.1-8b-instant",        # Быстрая модель (8B, 128k context)
                "llama-3.2-1b-preview",        # Легкая модель для тестирования
                "mixtral-8x7b-32768",          # Альтернатива от Mistral
            ]
            self.model = self.groq_models[0]
            self.model_index = 0
            self.provider = "groq"
        elif openai_api_key:
            self.client = AsyncOpenAI(api_key=openai_api_key)
            self.model = "gpt-4o-mini"
            self.provider = "openai"
        else:
            raise ValueError(
                "Необходимо установить GROQ_API_KEY или OPENAI_API_KEY в .env файле.\n"
                "Groq (бесплатный): https://console.groq.com/\n"
                "OpenAI: https://platform.openai.com/api-keys"
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

    def _handle_api_error(self, error: Exception) -> None:
        """Обрабатывает ошибки API и выбрасывает понятные исключения."""
        error_str = str(error)
        error_lower = error_str.lower()
        
        # Обработка ошибок лимитов
        if "insufficient_quota" in error_lower or "429" in error_str:
            raise ValueError(
                f"Превышен лимит запросов к {self.provider.upper()} API. "
                f"Проверьте лимиты на https://console.groq.com/" if self.provider == "groq" else "Проверьте лимиты на https://platform.openai.com/"
            )
        # Обработка ошибок аутентификации
        elif "invalid_api_key" in error_lower or "401" in error_str or "authentication" in error_lower:
            provider_name = "Groq" if self.provider == "groq" else "OpenAI"
            raise ValueError(
                f"Неверный API ключ {provider_name}. Проверьте:\n"
                f"1. Правильность ключа в .env файле ({self.provider.upper()}_API_KEY=...)\n"
                f"2. Что ключ скопирован полностью без пробелов\n"
                f"3. Получите новый ключ на https://console.groq.com/keys" if self.provider == "groq" else "3. Получите новый ключ на https://platform.openai.com/api-keys"
            )
        # Обработка ошибки 403 Forbidden
        elif "403" in error_str or "forbidden" in error_lower:
            if self.provider == "groq":
                raise ValueError(
                    "Доступ запрещен (403 Forbidden) к Groq API. Возможные причины:\n"
                    "1. Неверный API ключ - проверьте правильность в .env\n"
                    "2. Модель недоступна - попробуйте другую модель\n"
                    "3. Превышен лимит доступа - проверьте на https://console.groq.com/\n"
                    "4. Аккаунт заблокирован - свяжитесь с поддержкой Groq\n\n"
                    "Проверьте доступные модели: https://console.groq.com/docs/models"
                )
            else:
                raise ValueError(
                    "Доступ запрещен (403 Forbidden) к OpenAI API. Проверьте:\n"
                    "1. Правильность API ключа\n"
                    "2. Лимиты и доступность на https://platform.openai.com/"
                )
        # Обработка устаревших моделей
        elif "model_decommissioned" in error_lower or ("model" in error_lower and "decommissioned" in error_lower):
            raise ValueError(
                f"Модель {self.provider} устарела или недоступна. "
                f"Перезапустите бота. Если ошибка сохраняется, проверьте доступные модели на "
                f"https://console.groq.com/docs/models" if self.provider == "groq" else "https://platform.openai.com/docs/models"
            )
        # Обработка недоступности модели
        elif "model_not_found" in error_lower or "does not exist" in error_lower:
            raise ValueError(
                f"Модель '{self.model}' не найдена в {self.provider.upper()}. "
                f"Проверьте доступные модели и обновите код."
            )
        # Общая обработка ошибок
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка API ({self.provider}): {error_str}")
            raise ValueError(
                f"Ошибка при обработке запроса ({self.provider}): {error_str}\n"
                f"Проверьте настройки API ключа и доступность сервиса."
            )

    async def text_to_sql(self, user_query: str) -> str:
        """
        Преобразует текстовый запрос на русском языке в SQL.

        Args:
            user_query: Вопрос пользователя на русском языке

        Returns:
            SQL запрос в виде строки
        """
        max_retries = 3 if self.provider == "groq" and hasattr(self, 'groq_models') else 1
        
        for attempt in range(max_retries):
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
                error_lower = error_str.lower()
                
                # Если ошибка связана с моделью и есть альтернативные модели - пробуем следующую
                if (self.provider == "groq" and hasattr(self, 'groq_models') and 
                    attempt < max_retries - 1 and 
                    ("403" in error_str or "forbidden" in error_lower or 
                     "model_not_found" in error_lower or "does not exist" in error_lower)):
                    self.model_index = (self.model_index + 1) % len(self.groq_models)
                    self.model = self.groq_models[self.model_index]
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Пробуем альтернативную модель Groq: {self.model}")
                    continue
                
                # Если не удалось переключиться или это не ошибка модели - обрабатываем ошибку
                self._handle_api_error(e)