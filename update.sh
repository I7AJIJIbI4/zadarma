#!/bin/bash

echo "🔄 ОНОВЛЕННЯ ZADARMA BOT НА СЕРВЕРІ"
echo "=================================="

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/home/gomoncli/zadarma"
BACKUP_DIR="/home/gomoncli/backup/zadarma_update_$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}📁 Оновлення проєкту: $PROJECT_DIR${NC}"

# Перевірка чи існує проєкт
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ ПОМИЛКА: Проєкт не знайдено в $PROJECT_DIR${NC}"
    exit 1
fi

cd "$PROJECT_DIR" || exit 1

# 1. Створення backup важливих файлів
echo -e "${YELLOW}1️⃣ Створення backup важливих файлів...${NC}"
mkdir -p "$BACKUP_DIR"

# Бекапимо тільки важливі файли які не в Git
if [ -f "config.py" ]; then
    cp config.py "$BACKUP_DIR/"
    echo -e "   💾 config.py"
fi

if [ -f "users.db" ]; then
    cp users.db "$BACKUP_DIR/"
    echo -e "   💾 users.db"
fi

if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/"
    echo -e "   💾 .env"
fi

# Бекапимо логи
cp *.log "$BACKUP_DIR/" 2>/dev/null && echo -e "   💾 *.log"

echo -e "${GREEN}✅ Backup створено: $BACKUP_DIR${NC}"

# 2. Зупинення бота
echo -e "${YELLOW}2️⃣ Зупинення бота...${NC}"
BOT_PIDS=$(pgrep -f "python3.*bot.py")
if [ -n "$BOT_PIDS" ]; then
    echo -e "   🛑 Зупиняємо бота (PID: $BOT_PIDS)"
    pkill -f "python3.*bot.py"
    sleep 3
    
    # Перевіряємо чи зупинився
    if pgrep -f "python3.*bot.py" > /dev/null; then
        echo -e "${RED}   ⚠️ Бот не зупинився, примусове завершення...${NC}"
        pkill -9 -f "python3.*bot.py"
        sleep 2
    fi
    echo -e "${GREEN}   ✅ Бот зупинено${NC}"
else
    echo -e "   ℹ️ Бот не був запущений"
fi

# 3. Перевірка Git статусу
echo -e "${YELLOW}3️⃣ Перевірка Git статусу...${NC}"

# Перевіряємо чи це Git репозиторій
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ ПОМИЛКА: Це не Git репозиторій${NC}"
    echo -e "${YELLOW}Ініціалізуємо Git...${NC}"
    git init
    git remote add origin https://github.com/ваш-username/zadarma-bot.git
fi

# Показуємо статус
git status --porcelain
CHANGED_FILES=$(git status --porcelain | wc -l)

if [ "$CHANGED_FILES" -gt 0 ]; then
    echo -e "${YELLOW}   ⚠️ Знайдено $CHANGED_FILES змінених файлів${NC}"
    echo -e "${BLUE}   📋 Збережемо локальні зміни у stash...${NC}"
    git stash push -m "Auto stash before update $(date)"
else
    echo -e "${GREEN}   ✅ Робоча директорія чиста${NC}"
fi

# 4. Оновлення коду з GitHub
echo -e "${YELLOW}4️⃣ Оновлення з GitHub...${NC}"

# Встановлюємо remote якщо його немає
git remote get-url origin >/dev/null 2>&1 || {
    echo -e "${BLUE}   🔗 Додаємо remote origin...${NC}"
    git remote add origin https://github.com/ваш-username/zadarma-bot.git
}

# Завантажуємо зміни
git fetch origin main

# Показуємо що буде оновлено
COMMITS_BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
if [ "$COMMITS_BEHIND" -gt 0 ]; then
    echo -e "${BLUE}   📥 Доступно $COMMITS_BEHIND нових коммітів:${NC}"
    git log --oneline HEAD..origin/main | head -5
else
    echo -e "${GREEN}   ✅ Код вже актуальний${NC}"
fi

# КРИТИЧНО: Тимчасово зберігаємо config.py
echo -e "${BLUE}   💾 Тимчасово зберігаємо config.py...${NC}"
if [ -f "config.py" ]; then
    cp config.py /tmp/zadarma_config_temp.py
    echo -e "   ✅ config.py збережено в /tmp/"
fi

# Застосовуємо оновлення
echo -e "${BLUE}   🔄 Застосовуємо оновлення...${NC}"
git reset --hard origin/main

# КРИТИЧНО: Відновлюємо config.py
echo -e "${BLUE}   🔄 Відновлюємо config.py...${NC}"
if [ -f "/tmp/zadarma_config_temp.py" ]; then
    cp /tmp/zadarma_config_temp.py config.py
    rm -f /tmp/zadarma_config_temp.py
    echo -e "   ✅ config.py відновлено"
else
    echo -e "   ⚠️ Тимчасовий config.py не знайдено"
fi

echo -e "${GREEN}✅ Код оновлено${NC}"

# 5. Відновлення важливих файлів з backup
echo -e "${YELLOW}5️⃣ Відновлення конфігурації...${NC}"

if [ -f "$BACKUP_DIR/config.py" ]; then
    cp "$BACKUP_DIR/config.py" config.py
    echo -e "   ✅ config.py відновлено з backup"
elif [ -f "config.py" ]; then
    echo -e "   ✅ config.py вже існує (залишаємо поточний)"
else
    echo -e "${RED}   ❌ config.py відсутній!${NC}"
    if [ -f "config.py.example" ]; then
        echo -e "${YELLOW}   📝 Створюємо config.py з шаблону...${NC}"
        cp config.py.example config.py
        echo -e "${YELLOW}   ⚠️  УВАГА: Відредагуйте config.py з реальними API ключами!${NC}"
        echo -e "${BLUE}   nano config.py${NC}"
        echo -e "${YELLOW}   Натисніть Enter після редагування config.py...${NC}"
        read -r
    else
        echo -e "${RED}   ❌ Ні backup, ні шаблон не знайдено!${NC}"
        exit 1
    fi
fi

if [ -f "$BACKUP_DIR/users.db" ]; then
    cp "$BACKUP_DIR/users.db" users.db
    echo -e "   ✅ users.db відновлено"
fi

if [ -f "$BACKUP_DIR/.env" ]; then
    cp "$BACKUP_DIR/.env" .env
    echo -e "   ✅ .env відновлено"
fi

# 6. Перевірка конфігурації
echo -e "${YELLOW}6️⃣ Перевірка конфігурації...${NC}"

if [ ! -f "config.py" ]; then
    echo -e "${RED}❌ КРИТИЧНА ПОМИЛКА: Відсутній config.py${NC}"
    echo -e "${YELLOW}Створіть config.py перед продовженням:${NC}"
    echo -e "${BLUE}cp config.py.example config.py${NC}"
    echo -e "${BLUE}nano config.py${NC}"
    exit 1
fi

# Тестуємо конфігурацію
if python3 -c "from config import validate_config; validate_config()" 2>/dev/null; then
    echo -e "${GREEN}✅ Конфігурація валідна${NC}"
else
    echo -e "${RED}❌ ПОМИЛКА: Некоректна конфігурація${NC}"
    echo -e "${YELLOW}Перевірте файл config.py та виправте помилки${NC}"
    exit 1
fi

# 7. Оновлення залежностей
echo -e "${YELLOW}7️⃣ Оновлення залежностей...${NC}"
pip3 install -r requirements.txt --user --upgrade
echo -e "${GREEN}✅ Залежності оновлено${NC}"

# 8. Налаштування прав доступу
echo -e "${YELLOW}8️⃣ Налаштування прав...${NC}"
chmod +x *.sh *.py
chmod -R 755 webhooks/ 2>/dev/null || true
echo -e "${GREEN}✅ Права налаштовано${NC}"

# 9. Перевірка API (швидка)
echo -e "${YELLOW}9️⃣ Швидка перевірка API...${NC}"
if [ -f "api_check.sh" ]; then
    timeout 30 ./api_check.sh || echo -e "${YELLOW}   ⚠️ Деякі API недоступні (може бути нормально)${NC}"
else
    echo -e "   ℹ️ Скрипт api_check.sh не знайдено"
fi

# 10. Запуск бота
echo -e "${YELLOW}🔟 Запуск оновленого бота...${NC}"

if [ -f "run_script.sh" ]; then
    nohup ./run_script.sh > /dev/null 2>&1 &
    BOT_PID=$!
    echo -e "   🚀 Бот запущено (PID: $BOT_PID)"
    
    # Чекаємо 5 секунд та перевіряємо
    sleep 5
    if kill -0 $BOT_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Бот успішно працює${NC}"
    else
        echo -e "${RED}❌ Бот не запустився, перевірте логи:${NC}"
        tail -10 bot.log 2>/dev/null || echo "Лог файл відсутній"
        exit 1
    fi
else
    echo -e "${YELLOW}   ⚠️ run_script.sh не знайдено, запускаємо напряму:${NC}"
    nohup python3 bot.py > /dev/null 2>&1 &
    echo -e "   🚀 Бот запущено"
fi

# 11. Очищення старих backup'ів (залишаємо тільки останні 5)
echo -e "${YELLOW}1️⃣1️⃣ Очищення старих backup'ів...${NC}"
BACKUP_BASE_DIR="$(dirname "$BACKUP_DIR")"
if [ -d "$BACKUP_BASE_DIR" ]; then
    ls -1t "$BACKUP_BASE_DIR"/zadarma_update_* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
    REMAINING_BACKUPS=$(ls -1 "$BACKUP_BASE_DIR"/zadarma_update_* 2>/dev/null | wc -l)
    echo -e "   🗑️ Залишено $REMAINING_BACKUPS останніх backup'ів"
fi

echo ""
echo -e "${GREEN}🎉 ОНОВЛЕННЯ ЗАВЕРШЕНО УСПІШНО!${NC}"
echo ""
echo -e "${BLUE}📋 ПІДСУМОК:${NC}"
echo -e "   📁 Проєкт:        $PROJECT_DIR"
echo -e "   💾 Backup:        $BACKUP_DIR"
echo -e "   🤖 Bot PID:       $(pgrep -f "python3.*bot.py" || echo "не знайдено")"
echo -e "   📊 Коммітів:      $COMMITS_BEHIND нових"
echo ""
echo -e "${BLUE}🔍 ПЕРЕВІРКА:${NC}"
echo -e "   Статус бота:      ps aux | grep bot.py"
echo -e "   Логи бота:        tail -f bot.log"
echo -e "   Webhook логи:     tail -f webhook_processor.log"
echo -e "   Процеси:          pgrep -f python3.*bot.py"
echo ""
echo -e "${GREEN}✅ Бот оновлено та запущено!${NC}"
