# Быстрая загрузка данных в базу

## Вариант 1: Через HTTP endpoint (после перезапуска сервиса)

Дождитесь, пока Render перезапустит сервис с новым кодом (обычно 2-3 минуты после push).

Затем откройте в браузере:
```
https://tg-bot-gyct.onrender.com/load-data
```

Или через curl:
```bash
curl https://tg-bot-gyct.onrender.com/load-data
```

## Вариант 2: Локальная загрузка (если есть DATABASE_URL)

Если у вас есть доступ к DATABASE_URL, можно загрузить данные локально:

1. Создайте файл `.env` в корне проекта:
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

2. Запустите скрипт:
```bash
python load_data_direct.py
```

Или используйте setup_db.py напрямую:
```bash
python setup_db.py
```

## Вариант 3: Через Python скрипт с requests

1. Установите requests:
```bash
pip install requests
```

2. Запустите:
```bash
python load_data_remote.py
```

## Проверка загрузки

После загрузки проверьте в Telegram:
- Отправьте боту: "Сколько всего видео есть в системе?"
- Бот должен вернуть число (например: `1234`)
