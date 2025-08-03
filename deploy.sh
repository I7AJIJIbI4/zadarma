#!/bin/bash

echo "🚀 РОЗГОРТАННЯ ZADARMA BOT НА СЕРВЕРІ"
echo "====================================="

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/home/gomoncli/zadarma"
BACKUP_DIR="/home/gomoncli/backup/zadarma_$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}📁 Робочий каталог: $PROJECT_DIR${NC}"

# 1. Створення backup існуючого проєкту
if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}1️⃣ Створення backup...${NC}"
    mkdir -p "$(dirname "$BACKUP_DIR")"
    cp -r "$PROJECT_DIR" "$BACKUP_DIR"
    echo -e "${GREEN}✅ Backup створено: $BACKUP_DIR${NC}"
fi

# 2. Зупинення бота
echo -e "${YELLOW}2️⃣ Зупинення старого бота...${NC}"
pkill -f "python3.*bot.py" || echo "Бот не був запущений"

# 3. Оновлення з Git
echo -e "${YELLOW}3️⃣ Оновлення коду з Git...${NC}"
cd "$PROJECT_DIR" || exit 1

git fetch origin
git reset --hard origin/main
echo -e "${GREEN}✅ Код оновлено${NC}"

# 4. Перевірка конфігурації
echo -e "${YELLOW}4️⃣ Перевірка конфігурації...${NC}"
if [ ! -f "config.py" ]; then
    echo -e "${RED}❌ ПОМИЛКА: Відсутній файл config.py${NC}"
    echo -e "${YELLOW}Скопіюйте config.py.example в config.py та заповніть реальними данними${NC}"
    echo -e "${BLUE}cp config.py.example config.py${NC}"
    echo -e "${BLUE}nano config.py${NC}"
    exit 1
fi

# Тестування конфігурації
python3 -c "from config import validate_config; validate_config()" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Конфігурація валідна${NC}"
else
    echo -e "${RED}❌ ПОМИЛКА: Конфігурація містить помилки${NC}"
    echo -e "${YELLOW}Перевірте файл config.py${NC}"
    exit 1
fi

# 5. Встановлення залежностей
echo -e "${YELLOW}5️⃣ Встановлення залежностей...${NC}"
pip3 install -r requirements.txt --user
echo -e "${GREEN}✅ Залежності встановлено${NC}"

# 6. Перевірка прав доступу
echo -e "${YELLOW}6️⃣ Налаштування прав доступу...${NC}"
chmod +x *.sh
chmod +x *.py
chmod -R 755 webhooks/
echo -e "${GREEN}✅ Права налаштовано${NC}"

# 7. Перевірка API
echo -e "${YELLOW}7️⃣ Перевірка API сервісів...${NC}"
./api_check.sh
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ API сервіси доступні${NC}"
else
    echo -e "${YELLOW}⚠️ Деякі API сервіси недоступні (може бути нормально)${NC}"
fi

# 8. Запуск бота
echo -e "${YELLOW}8️⃣ Запуск бота...${NC}"
./run_script.sh &
BOT_PID=$!

# Чекаємо 5 секунд та перевіряємо чи бот запустився
sleep 5
if kill -0 $BOT_PID 2>/dev/null; then
    echo -e "${GREEN}✅ Бот успішно запущений (PID: $BOT_PID)${NC}"
else
    echo -e "${RED}❌ ПОМИЛКА: Бот не запустився${NC}"
    echo -e "${YELLOW}Перевірте логи:${NC}"
    tail -20 bot.log 2>/dev/null || echo "Лог файл відсутній"
    exit 1
fi

# 9. Налаштування cron (якщо потрібно)
echo -e "${YELLOW}9️⃣ Перевірка cron завдань...${NC}"
CRON_EXISTS=$(crontab -l 2>/dev/null | grep -c "zadarma" || echo "0")
if [ "$CRON_EXISTS" -eq 0 ]; then
    echo -e "${BLUE}Додаємо cron завдання...${NC}"
    (crontab -l 2>/dev/null; echo "*/5 * * * * $PROJECT_DIR/check_and_run_bot.sh >> $PROJECT_DIR/cron.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "0 6 * * * $PROJECT_DIR/daily_maintenance.sh >> $PROJECT_DIR/maintenance.log 2>&1") | crontab -
    echo -e "${GREEN}✅ Cron завдання додано${NC}"
else
    echo -e "${GREEN}✅ Cron завдання вже налаштовані${NC}"
fi

echo ""
echo -e "${GREEN}🎉 РОЗГОРТАННЯ ЗАВЕРШЕНО УСПІШНО!${NC}"
echo ""
echo -e "${BLUE}📋 ІНФОРМАЦІЯ:${NC}"
echo -e "   📁 Проєкт: $PROJECT_DIR"
echo -e "   💾 Backup: $BACKUP_DIR"
echo -e "   🤖 Bot PID: $BOT_PID"
echo ""
echo -e "${BLUE}🔍 КОРИСНІ КОМАНДИ:${NC}"
echo -e "   Статус бота:     ps aux | grep bot.py"
echo -e "   Логи бота:       tail -f $PROJECT_DIR/bot.log"
echo -e "   Webhook логи:    tail -f $PROJECT_DIR/webhook_processor.log"
echo -e "   Перевірка API:   $PROJECT_DIR/api_check.sh"
echo -e "   Зупинка бота:    pkill -f 'python3.*bot.py'"
echo ""
echo -e "${YELLOW}⚠️ ВАЖЛИВО: Переконайтеся що webhook налаштовано в кабінеті Zadarma!${NC}"
echo -e "   URL: https://ваш-домен.com/webhooks/zadarma_webhook.php"
