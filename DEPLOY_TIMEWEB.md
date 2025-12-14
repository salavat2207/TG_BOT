# Инструкция по развертыванию на Timeweb

## Вариант 1: Docker контейнеры (рекомендуется)

### 1. Подготовка на Timeweb

1. Создайте контейнер PostgreSQL в панели Timeweb
2. Создайте контейнер для бота (выберите образ из Dockerfile)

### 2. Настройка переменных окружения

В настройках контейнера бота добавьте переменные окружения:

```
DATABASE_URL=postgresql://user:password@host:port/database
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_groq_api_key
# или
OPENAI_API_KEY=your_openai_api_key
```

### 3. Инициализация базы данных

После запуска контейнера выполните:

```bash
docker exec -it tg_bot python setup_db.py
```

Или через Shell в панели Timeweb выполните команду:
```bash
python setup_db.py
```

## Вариант 2: VPS с Docker Compose

### 1. Подключение к VPS

```bash
ssh user@your-timeweb-vps
```

### 2. Клонирование репозитория

```bash
git clone https://github.com/salavat2207/TG_BOT.git
cd TG_BOT
```

### 3. Создание .env файла

```bash
cp .env.example .env
nano .env
```

Заполните переменные:
```
TELEGRAM_BOT_TOKEN=your_token
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/video_analytics
GROQ_API_KEY=your_key
```

### 4. Запуск через Docker Compose

```bash
docker-compose up -d
```

### 5. Инициализация базы данных

```bash
docker-compose exec bot python setup_db.py
```

## Вариант 3: Прямой запуск на VPS

### 1. Установка зависимостей

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

```bash
export DATABASE_URL=postgresql://user:password@host:port/database
export TELEGRAM_BOT_TOKEN=your_token
export GROQ_API_KEY=your_key
```

### 3. Инициализация БД

```bash
python setup_db.py
```

### 4. Запуск бота

```bash
python main.py
```

Или через systemd для автозапуска:

```bash
sudo nano /etc/systemd/system/tg-bot.service
```

Содержимое файла:
```ini
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/TG_BOT
Environment="DATABASE_URL=postgresql://..."
Environment="TELEGRAM_BOT_TOKEN=..."
Environment="GROQ_API_KEY=..."
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Активация:
```bash
sudo systemctl enable tg-bot
sudo systemctl start tg-bot
```

## Проверка работы

После развертывания проверьте логи:

```bash
# Для Docker
docker-compose logs -f bot

# Для systemd
sudo journalctl -u tg-bot -f
```

Бот должен ответить на команду `/start` в Telegram.
