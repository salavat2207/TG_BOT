# Инструкция по локальному запуску бота

## Быстрый старт

### 1. Запуск локальной базы данных

```bash
docker-compose up -d postgres
```

### 2. Загрузка данных (если еще не загружены)

```bash
source .venv/bin/activate  # или source venv/bin/activate
export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/video_analytics"
python setup_db.py
```

### 3. Запуск бота

**Вариант 1: Через скрипт**
```bash
./run_local.sh
```

**Вариант 2: Вручную**
```bash
source .venv/bin/activate  # или source venv/bin/activate
export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/video_analytics"
python main.py
```

**Вариант 3: Через docker-compose (полный стек)**
```bash
docker-compose up
```

## Важно

- Для локального запуска используйте: `postgresql://postgres:postgres@localhost:5433/video_analytics`
- Для Render используйте Internal Database URL из настроек PostgreSQL
- Убедитесь, что в `.env` есть `TELEGRAM_BOT_TOKEN` и `GEMINI_API_KEY`

## Проверка работы

1. Откройте Telegram
2. Найдите вашего бота
3. Отправьте `/start`
4. Отправьте вопрос: "Сколько всего видео есть в системе?"
5. Бот должен вернуть число (например: `358`)
