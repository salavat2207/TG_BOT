#!/bin/bash
# Скрипт для локального запуска бота

# Освобождение порта 8000, если он занят
PORT=8000
PID=$(lsof -ti:$PORT 2>/dev/null)
if [ ! -z "$PID" ]; then
    echo "Освобождаю порт $PORT (процесс $PID)..."
    kill -9 $PID 2>/dev/null
    sleep 1
fi

# Активация виртуального окружения
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Установка DATABASE_URL для локальной БД
export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/video_analytics"

# Запуск бота
python main.py
