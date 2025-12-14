#!/bin/bash
# Скрипт для локального запуска бота

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
