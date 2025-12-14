"""Скрипт для загрузки данных через HTTP endpoint на Render."""
import requests
import sys

# URL вашего сервиса на Render
SERVICE_URL = "https://tg-bot-gyct.onrender.com/load-data"

def load_data():
    """Загружает данные через HTTP endpoint."""
    print(f"Отправка запроса на {SERVICE_URL}...")
    
    try:
        response = requests.get(SERVICE_URL, timeout=300)  # 5 минут таймаут
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Успех: {result.get('message', 'Данные загружены')}")
            return True
        else:
            print(f"❌ Ошибка: HTTP {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️ Таймаут запроса (загрузка может занять больше времени)")
        print("Проверьте логи на Render для деталей")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Загрузка данных в базу данных на Render")
    print("=" * 50)
    print()
    
    success = load_data()
    
    if success:
        print()
        print("=" * 50)
        print("✅ Данные успешно загружены!")
        print("Бот готов к работе. Проверьте его в Telegram.")
        print("=" * 50)
        sys.exit(0)
    else:
        print()
        print("=" * 50)
        print("❌ Ошибка при загрузке данных")
        print("Проверьте логи на Render для деталей")
        print("=" * 50)
        sys.exit(1)
