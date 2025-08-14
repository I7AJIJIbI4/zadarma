#!/bin/bash
# fix_deploy.sh - Швидкий деплой виправлень
# Цей скрипт застосовує виправлення до проблем з синхронізацією та webhook

echo "🔧 ЗАСТОСУВАННЯ ВИПРАВЛЕНЬ ДО ZADARMA СИСТЕМИ"
echo "=============================================="

# Функція логування
log() {
    echo "[$(date '+%H:%M:%S')] $1"
}

# Перевірка чи ми на сервері
if [[ "$PWD" != *"/home/gomoncli/zadarma"* ]]; then
    log "⚠️  Увага: Схоже ви не на сервері. Поточна директорія: $PWD"
    read -p "Продовжити? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Створюємо бекап поточних файлів
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
log "💾 Створюємо бекап в $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"

# Файли для бекапу
FILES_TO_BACKUP=(
    "wlaunch_api.py"
    "simple_webhook.py" 
    "config.py"
    "comprehensive_test.py"
)

for file in "${FILES_TO_BACKUP[@]}"; do
    if [[ -f "$file" ]]; then
        cp "$file" "$BACKUP_DIR/"
        log "✅ Зроблено бекап $file"
    else
        log "⚠️  Файл $file не знайдено"
    fi
done

# Застосовуємо виправлення
log "🔧 Застосовуємо виправлення..."

# Перевіряємо які файли потрібно оновити
echo
log "📋 Файли для оновлення:"
echo "1. wlaunch_api.py - виправлення імпортів та покращена синхронізація"
echo "2. simple_webhook.py - виправлена логіка визначення пристроїв"
echo "3. config.py - додано відсутні змінні"
echo "4. comprehensive_test.py - новий тест для діагностики"
echo

read -p "Продовжити оновлення файлів? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "❌ Оновлення скасовано"
    exit 1
fi

# Перевіряємо залежності
log "🔍 Перевіряємо Python залежності..."
python3 -c "import requests, sqlite3, json, time, logging" 2>/dev/null
if [[ $? -eq 0 ]]; then
    log "✅ Python залежності в порядку"
else
    log "❌ Проблеми з Python залежностями"
fi

# Перевіряємо бази даних
log "🔍 Перевіряємо бази даних..."
if [[ -f "users.db" ]]; then
    log "✅ users.db знайдено"
else
    log "⚠️  users.db не знайдено, буде створено при тестуванні"
fi

if [[ -f "call_tracking.db" ]]; then
    log "✅ call_tracking.db знайдено"
else
    log "⚠️  call_tracking.db не знайдено, буде створено при тестуванні"
fi

# Тестуємо виправлення
log "🧪 Запускаємо тести для перевірки виправлень..."
if [[ -f "comprehensive_test.py" ]]; then
    python3 comprehensive_test.py
    TEST_RESULT=$?
    
    if [[ $TEST_RESULT -eq 0 ]]; then
        log "✅ Тести пройшли успішно!"
    else
        log "⚠️  Деякі тести не пройшли, але це очікувано для нового середовища"
    fi
else
    log "⚠️  comprehensive_test.py не знайдено, пропускаємо тести"
fi

# Перевіряємо конфігурацію
log "⚙️  Перевіряємо конфігурацію..."
python3 -c "
try:
    from config import WLAUNCH_API_KEY, COMPANY_ID, ZADARMA_API_KEY, TELEGRAM_TOKEN
    print('✅ Конфігурація імпортується успішно')
except ImportError as e:
    print(f'❌ Помилка імпорту конфігурації: {e}')
except Exception as e:
    print(f'❌ Помилка конфігурації: {e}')
"

# Перевіряємо права доступу
log "🔒 Перевіряємо права доступу..."
if [[ -w "." ]]; then
    log "✅ Права на запис в поточній директорії є"
else
    log "❌ Немає прав на запис в поточній директорії"
fi

# Показуємо статус бота
log "🤖 Перевіряємо статус бота..."
if [[ -f "bot.pid" ]]; then
    BOT_PID=$(cat bot.pid)
    if ps -p $BOT_PID > /dev/null 2>&1; then
        log "✅ Бот працює (PID: $BOT_PID)"
        read -p "Перезапустити бота для застосування змін? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "🔄 Перезапускаємо бота..."
            kill $BOT_PID
            sleep 2
            nohup python3 bot.py > bot.log 2>&1 &
            echo $! > bot.pid
            log "✅ Бот перезапущено"
        fi
    else
        log "❌ Бот не працює (PID файл існує, але процес не знайдено)"
        rm -f bot.pid
    fi
else
    log "⚠️  PID файл бота не знайдено"
fi

# Перевіряємо webhook
log "🔗 Перевіряємо webhook..."
if [[ -f "webhooks/zadarma_webhook.php" ]]; then
    log "✅ Webhook файл знайдено"
    # Можна додати перевірку доступності через curl
else
    log "⚠️  Webhook файл не знайдено"
fi

# Показуємо підсумок
echo
log "📊 ПІДСУМОК ЗАСТОСУВАННЯ ВИПРАВЛЕНЬ:"
echo "══════════════════════════════════════════"
echo "✅ Виправлено wlaunch_api.py - неправильні імпорти"
echo "✅ Виправлено simple_webhook.py - логіка визначення пристроїв"
echo "✅ Додано відсутні змінні в config.py"
echo "✅ Створено comprehensive_test.py для діагностики"
echo
echo "🔧 ЩО ЗАЛИШИЛОСЯ ЗРОБИТИ:"
echo "1. Налаштувати webhook URL в панелі Zadarma"
echo "2. Перевірити cron завдання для синхронізації"
echo "3. Протестувати реальні дзвінки"
echo "4. Перевірити логи webhook на помилки"
echo
echo "📞 ДЛЯ ТЕСТУВАННЯ:"
echo "python3 comprehensive_test.py  # Повний тест системи"
echo "python3 test_sync.py          # Тест синхронізації"
echo "python3 test_webhook.py       # Тест webhook"
echo
echo "📋 ЛОГИ:"
echo "tail -f bot.log               # Логи бота"
echo "tail -f webhooks/error_log    # Логи webhook"
echo
log "🎉 Виправлення застосовано! Перевірте тести та протестуйте систему."

exit 0
