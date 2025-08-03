# 🏠 Zadarma Gate Control Bot

Telegram бот для управління хвірткою та воротами через Zadarma API.

## 🚀 Швидкий старт

### 1. Клонування проєкту
```bash
git clone https://github.com/YOUR_USERNAME/zadarma-bot.git
cd zadarma-bot
```

### 2. Налаштування конфігурації
```bash
# Скопіюйте шаблон конфігурації
cp config.py.example config.py

# Відредагуйте конфігурацію з вашими реальними данними
nano config.py
```

### 3. Встановлення залежностей
```bash
# Встановлення Python пакетів
pip3 install -r requirements.txt
```

### 4. Налаштування бази даних
База даних SQLite створюється автоматично при першому запуску.

### 5. Запуск бота
```bash
# Запуск через скрипт
./run_script.sh

# Або безпосередньо
python3 bot.py
```

## ⚙️ Конфігурація

Заповніть файл `config.py` наступними данними:

### Telegram Bot
- `TELEGRAM_TOKEN` - токен від @BotFather
- `ADMIN_USER_ID` - ваш Telegram User ID

### Zadarma API
- `ZADARMA_API_KEY` - ключ API з кабінету Zadarma
- `ZADARMA_API_SECRET` - секретний ключ API
- `ZADARMA_SIP_ACCOUNT` - ваш SIP аккаунт
- `ZADARMA_MAIN_PHONE` - основний номер телефону
- `HVIRTKA_NUMBER` - номер хвіртки
- `VOROTA_NUMBER` - номер воріт

### WLaunch API (опціонально)
- `WLAUNCH_API_KEY` - ключ WLaunch API
- `COMPANY_ID` - ID компанії в WLaunch

### SMS Fly (опціонально)
- `SMS_FLY_LOGIN` - логін SMS Fly
- `SMS_FLY_PASSWORD` - пароль SMS Fly
- `SMS_FLY_SENDER` - ім'я відправника

## 🔧 Обслуговування

### Автоматичні скрипти
- `daily_maintenance.sh` - щоденне обслуговування
- `api_check.sh` - перевірка API
- `check_and_run_bot.sh` - перевірка та запуск бота

### Моніторинг
```bash
# Перевірка статусу всіх API
./api_check.sh

# Перевірка роботи бота
./check_and_run_bot.sh

# Денне обслуговування
./daily_maintenance.sh
```

### Логи
- `bot.log` - логи роботи бота
- `webhook_processor.log` - логи webhook обробника
- `maintenance.log` - логи обслуговування

## 🔗 Webhook налаштування

### PHP webhook файли в папці `webhooks/`:
- `zadarma_webhook.php` - основний webhook для Zadarma
- `zadarma_ivr_webhook_fixed.php` - IVR webhook
- `gomonclinic_webhook.php` - webhook для клініки

### Налаштування в Zadarma:
1. Зайдіть в кабінет Zadarma
2. API -> Webhooks
3. Додайте URL: `https://ваш-домен.com/webhooks/zadarma_webhook.php`

## 📱 Команди бота

### Для користувачів:
- `/start` - початок роботи з ботом
- `/hvirtka` - відкрити хвіртку
- `/vorota` - відкрити ворота
- `/info` - інформація про клініку
- `/map` - карта проїзду
- `/help` - допомога

### Для адміністраторів:
- `/admin` - панель адміністратора
- `/stats` - статистика використання
- `/users` - список користувачів
- `/sync` - синхронізація з WLaunch

## 🛠️ Розробка

### Структура проєкту
```
zadarma-bot/
├── bot.py                 # Головний файл бота
├── config.py.example      # Шаблон конфігурації
├── zadarma_api.py         # Zadarma API
├── zadarma_api_webhook.py # Webhook обробка
├── wlaunch_api.py         # WLaunch API
├── user_db.py             # Робота з базою даних
├── auth.py                # Авторизація
├── utils.py               # Допоміжні функції
├── process_webhook.py     # Обробник webhook
├── webhooks/              # PHP webhook файли
├── reports/               # Денні звіти
└── requirements.txt       # Python залежності
```

### Тестування
```bash
# Тестування форматування номерів
python3 config.py

# Тестування webhook
python3 process_webhook.py '{"event":"NOTIFY_END","caller_id":"test"}'
```

## 🔒 Безпека

- ✅ Конфіденційні дані в `config.py` не коммітяться в Git
- ✅ API ключі зберігаються локально
- ✅ Логи не містять чутливої інформації
- ✅ Webhook захищений від зловмисних запитів

## 📞 Підтримка

При виникненні проблем зверніться до:
- Телефон: `SUPPORT_PHONE` з config.py
- Email: admin@example.com
- Telegram: @admin

## 📄 Ліцензія

MIT License - детальніше в файлі LICENSE.
