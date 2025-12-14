# Telegram-бот для аналитики по видео

Telegram-бот, который обрабатывает запросы на естественном языке и возвращает аналитику по видео из базы данных PostgreSQL.

## Описание

Бот принимает текстовые запросы на русском языке, преобразует их в SQL-запросы с помощью LLM (Groq API - бесплатный, или OpenAI API) и возвращает числовые результаты из базы данных.

## Архитектура

### Компоненты:

1. **База данных PostgreSQL** - хранит данные о видео и почасовых снапшотах статистики
2. **Модуль NLP (nlp_handler.py)** - преобразует естественный язык в SQL с помощью OpenAI API
3. **Модуль базы данных (database.py)** - управляет подключениями и выполнением SQL-запросов
4. **Telegram-бот (bot.py)** - обрабатывает сообщения пользователей

### Подход к преобразованию текста в SQL:

Используется LLM (Groq LLaMA 3.1 70B - бесплатный, или OpenAI GPT-4o-mini) с детальным системным промптом, который:
- Описывает полную схему базы данных (таблицы `videos` и `video_snapshots`)
- Объясняет назначение каждого поля
- Содержит примеры преобразования типичных запросов
- Указывает правила работы с датами и агрегатными функциями

Промпт настроен на возврат только SQL-запроса без дополнительных пояснений, что обеспечивает стабильный парсинг результата.

## Требования

- Python 3.9+
- PostgreSQL 15+
- Docker и Docker Compose (опционально, для запуска БД)
- Telegram Bot Token
- **Groq API Key (бесплатный)** или OpenAI API Key

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <repository_url>
cd TG_BOT
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
# Используйте Groq API (бесплатный) или OpenAI API
GROQ_API_KEY=your_groq_api_key_here  # Получите на https://console.groq.com/ (бесплатно!)
# ИЛИ
# OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/video_analytics
```

**Как получить бесплатный Groq API ключ:**
1. Зарегистрируйтесь на https://console.groq.com/
2. Создайте новый API ключ в разделе API Keys
3. Скопируйте ключ и добавьте в `.env` файл как `GROQ_API_KEY`
4. Groq предоставляет бесплатный tier с щедрыми лимитами (30 запросов/минуту)

### 4. Запуск PostgreSQL

#### Вариант 1: С помощью Docker Compose (рекомендуется)

```bash
docker-compose up -d
```

#### Вариант 2: Локальная установка PostgreSQL

Установите PostgreSQL локально и создайте базу данных:

```sql
CREATE DATABASE video_analytics;
```

### 5. Инициализация базы данных

Выполните миграции для создания таблиц:

```bash
python init_db.py
```

### 6. Загрузка данных

Загрузите JSON-файл в базу данных:

```bash
python app/load_data.py
```

### 7. Запуск бота

```bash
python main.py
```

## Структура проекта

```
TG_BOT/
├── app/
│   ├── videos.json          # Исходные данные
│   └── load_data.py         # Скрипт загрузки данных в БД
├── bot/
│   ├── __init__.py
│   ├── bot.py               # Основной модуль Telegram-бота
│   ├── database.py          # Модуль работы с БД
│   └── nlp_handler.py       # Модуль обработки естественного языка
├── migrations/
│   └── 001_create_tables.sql # SQL миграции
├── .env                      # Переменные окружения (не в git)
├── .gitignore
├── docker-compose.yml        # Конфигурация Docker для PostgreSQL
├── init_db.py               # Скрипт инициализации БД
├── main.py                  # Точка входа
├── requirements.txt         # Зависимости Python
└── README.md
```

## Схема базы данных

### Таблица `videos`

Итоговая статистика по каждому видео:
- `id` (UUID) - идентификатор видео
- `creator_id` (VARCHAR) - идентификатор креатора
- `video_created_at` (TIMESTAMP) - дата публикации
- `views_count`, `likes_count`, `comments_count`, `reports_count` (INTEGER)
- `created_at`, `updated_at` (TIMESTAMP)

### Таблица `video_snapshots`

Почасовые замеры статистики:
- `id` (VARCHAR) - идентификатор снапшота
- `video_id` (UUID) - ссылка на видео
- `views_count`, `likes_count`, `comments_count`, `reports_count` (INTEGER) - текущие значения
- `delta_views_count`, `delta_likes_count`, `delta_comments_count`, `delta_reports_count` (INTEGER) - приращения
- `created_at`, `updated_at` (TIMESTAMP)

## Примеры запросов

Бот может отвечать на вопросы вида:

- "Сколько всего видео есть в системе?"
- "Сколько видео у креатора с id abc123 вышло с 1 ноября 2025 по 5 ноября 2025 включительно?"
- "Сколько видео набрало больше 100000 просмотров за всё время?"
- "На сколько просмотров в сумме выросли все видео 28 ноября 2025?"
- "Сколько разных видео получали новые просмотры 27 ноября 2025?"


