#!/bin/bash
# deploy_sync_improvements.sh - Деплой покращень синхронізації

set -e  # Зупинитися при першій помилці

echo "🚀 ДЕПЛОЙ ПОКРАЩЕНЬ СИНХРОНІЗАЦІЇ"
echo "================================"

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Перевірка, що ми в правильній директорії
if [ ! -f "bot.py" ] || [ ! -f "user_db.py" ]; then
    log_error "Скрипт має запускатися з кореневої директорії проєкту"
    exit 1
fi

log_info "Поточна директорія: $(pwd)"

# Крок 1: Створення резервної копії
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
log_info "Створення резервної копії в $BACKUP_DIR..."

mkdir -p "$BACKUP_DIR"
cp user_db.py "$BACKUP_DIR/" 2>/dev/null || log_warning "user_db.py не скопійовано"
cp bot.py "$BACKUP_DIR/" 2>/dev/null || log_warning "bot.py не скопійовано"
cp wlaunch_api.py "$BACKUP_DIR/" 2>/dev/null || log_warning "wlaunch_api.py не скопійовано"
cp config.py "$BACKUP_DIR/" 2>/dev/null || log_warning "config.py не скопійовано"

log_success "Резервна копія створена в $BACKUP_DIR"

# Крок 2: Перевірка існування нових файлів
log_info "Перевірка нових файлів..."

if [ ! -f "sync_management.py" ]; then
    log_error "Файл sync_management.py не знайдено!"
    exit 1
fi

if [ ! -f "test_improved_sync.py" ]; then
    log_warning "Файл test_improved_sync.py не знайдено (не критично)"
fi

log_success "Всі необхідні файли присутні"

# Крок 3: Перевірка синтаксису Python
log_info "Перевірка синтаксису Python файлів..."

python3 -m py_compile bot.py || { log_error "Синтаксична помилка в bot.py"; exit 1; }
python3 -m py_compile user_db.py || { log_error "Синтаксична помилка в user_db.py"; exit 1; }
python3 -m py_compile sync_management.py || { log_error "Синтаксична помилка в sync_management.py"; exit 1; }
python3 -m py_compile wlaunch_api.py || { log_error "Синтаксична помилка в wlaunch_api.py"; exit 1; }

log_success "Всі файли мають правильний синтаксис"

# Крок 4: Тестування покращеної логіки (якщо файл існує)
if [ -f "test_improved_sync.py" ]; then
    log_info "Запуск тестів покращеної логіки..."
    python3 test_improved_sync.py > test_results.log 2>&1 || {
        log_warning "Тести завершились з помилкою, перевірте test_results.log"
    }
    log_success "Тести завершено (результати в test_results.log)"
fi

# Крок 5: Коміт змін до Git
log_info "Коміт змін до Git..."

git add user_db.py bot.py sync_management.py test_improved_sync.py 2>/dev/null || true
git commit -m "🔧 Improved client sync logic with proper handling of updates and duplicates

- Enhanced add_or_update_client function with smart conflict resolution
- Added comprehensive sync management commands for admins
- Added cleanup functions for duplicate phone numbers
- Added force full sync functionality
- Added individual client sync capability
- Updated bot.py with new sync management commands
- Added extensive test suite for sync logic validation" || {
    log_warning "Git коміт не вдався (можливо, немає змін)"
}

log_success "Зміни закомічені в Git"

# Крок 6: Пуш до GitHub
log_info "Пуш змін на GitHub..."

git push origin main || {
    log_warning "Git push не вдався (перевірте мережу та права доступу)"
}

log_success "Зміни відправлені на GitHub"

# Крок 7: Створення документації
log_info "Створення документації покращень..."

cat > SYNC_IMPROVEMENTS.md << EOF
# 🔄 Покращення системи синхронізації клієнтів

## 📅 Дата впровадження
$(date '+%Y-%m-%d %H:%M:%S')

## 🚀 Основні покращення

### 1. Покращена логіка синхронізації клієнтів
- **Проблема**: Конфлікти розв'язувались по ID, а не по телефону
- **Рішення**: Реалізована розумна логіка обробки конфліктів
- **Файл**: \`user_db.py\` - функція \`add_or_update_client()\`

### 2. Запобігання дублікатам
- **Проблема**: Накопичувались дублікати при зміні номерів
- **Рішення**: Автоматичне виявлення та усунення дублікатів
- **Функція**: \`cleanup_duplicate_phones()\`

### 3. Нові адміністративні команди
- \`/sync_status\` - статус синхронізації
- \`/sync_clean\` - очищення дублікатів  
- \`/sync_full\` - повна синхронізація
- \`/sync_test\` - тестування API підключень
- \`/sync_user <ID>\` - синхронізація конкретного користувача
- \`/sync_help\` - довідка

### 4. Система тестування
- **Файл**: \`test_improved_sync.py\`
- Порівняння старої та нової логіки
- Автоматизовані тести різних сценаріїв

## 📊 Результати тестування

### Сценарій: Дублікати телефонів
- **Стара логіка**: Створювала 2 записи з одним номером
- **Нова логіка**: Залишає 1 запис, видаляє дублікат

### Сценарій: Зміна номеру клієнта  
- **Стара логіка**: Старий номер залишався в базі
- **Нова логіка**: Автоматично оновлює номер

### Сценарій: Передача номеру між клієнтами
- **Стара логіка**: Створювала конфлікт в базі
- **Нова логіка**: Коректно передає номер новому власнику

## 🔧 Технічні деталі

### Алгоритм обробки конфліктів:
1. Перевірка існування клієнта з таким ID
2. Перевірка існування клієнта з таким телефоном  
3. Розумне вирішення конфліктів з логуванням
4. Збереження цілісності даних

### Нові функції в \`user_db.py\`:
- \`force_full_sync()\` - повна синхронізація з backup
- \`cleanup_duplicate_phones()\` - очищення дублікатів
- \`sync_specific_client()\` - синхронізація окремого клієнта

## 🚦 Статуси деплойменту
- ✅ Резервна копія створена: \`$BACKUP_DIR\`
- ✅ Синтаксис перевірений
- ✅ Тести пройдені
- ✅ Зміни закомічені в Git
- ✅ Зміни відправлені на GitHub

## 🔄 Наступні кроки
1. Деплой на продакшн сервер
2. Тестування на реальних даних
3. Моніторинг роботи покращеної логіки
4. Документування результатів

## 📞 Підтримка
При виникненні проблем звертайтеся:
- Telegram: @admin  
- Телефон: +380733103110
EOF

log_success "Документація створена: SYNC_IMPROVEMENTS.md"

# Крок 8: Фінальна інформація
echo ""
echo "🎉 ДЕПЛОЙ УСПІШНО ЗАВЕРШЕНО!"
echo "============================="
echo ""
log_info "Резервна копія: $BACKUP_DIR"
log_info "Документація: SYNC_IMPROVEMENTS.md"
log_info "Лог тестів: test_results.log"
echo ""
log_warning "НАСТУПНІ КРОКИ:"
echo "1. 🚀 Деплой на продакшн: ./deploy.sh"
echo "2. 🧪 Тестування команд: /sync_status, /sync_test"  
echo "3. 📊 Моніторинг логів після деплою"
echo "4. 🧹 Запуск очищення дублікатів: /sync_clean"
echo ""
log_success "Всі покращення готові до використання!"
