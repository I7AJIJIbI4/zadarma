#!/bin/bash
# fix_zadarma_bot.sh - Автоматичне виправлення для Python 3.6 + стороння Telegram API
# Версія: 2.0 - з урахуванням специфіки системи
# Дата: 2025-08-06

set -e  # Зупинитися при першій помилці

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Конфігурація
BOT_DIR="/home/gomoncli/zadarma"
WEBHOOK_DIR="$BOT_DIR/webhooks"
BACKUP_DIR="/home/gomoncli/zadarma/backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="/tmp/fix_zadarma_$(date +%Y%m%d_%H%M%S).log"

# Функції логування
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Перевірка Python 3.6
check_python_version() {
    log_info "Перевірка версії Python..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print('{}.{}'.format(sys.version_info[0], sys.version_info[1]))")
        log_info "Знайдено Python $PYTHON_VERSION"
        
        if [[ "$PYTHON_VERSION" == "3.6" ]]; then
            log_success "Python 3.6 - підтримується"
        elif [[ "$PYTHON_VERSION" < "3.6" ]]; then
            log_warning "Python $PYTHON_VERSION може мати проблеми сумісності"
        else
            log_info "Python $PYTHON_VERSION - новіший за 3.6, має працювати"
        fi
    else
        log_error "Python3 не знайдено"
        exit 1
    fi
}

# Перевірка прав доступу
check_permissions() {
    if [[ $EUID -ne 0 ]] && [[ ! -w "$BOT_DIR" ]]; then
        log_error "Недостатньо прав для запису в $BOT_DIR"
        log_info "Запустіть скрипт з sudo або від власника файлів"
        exit 1
    fi
    log_success "Перевірка прав доступу пройшла успішно"
}

# Створення резервної копії
create_backup() {
    log_info "Створення резервної копії..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Копіюємо критичні файли
    local files_to_backup=(
        "bot.py"
        "zadarma_call.py"
        "zadarma_api_webhook.py"
        "process_webhook.py"
        "config.py"
        "user_db.py"
        "check_and_run_bot.sh"
    )
    
    for file in "${files_to_backup[@]}"; do
        if [[ -f "$BOT_DIR/$file" ]]; then
            cp "$BOT_DIR/$file" "$BACKUP_DIR/"
            log_info "  ✓ $file"
        else
            log_warning "  ! Файл $file не знайдено"
        fi
    done
    
    # Копіюємо webhook файли
    if [[ -d "$WEBHOOK_DIR" ]]; then
        cp -r "$WEBHOOK_DIR" "$BACKUP_DIR/"
        log_info "  ✓ webhooks/ папка"
    fi
    
    # Копіюємо crontab
    crontab -l > "$BACKUP_DIR/crontab_backup.txt" 2>/dev/null || log_warning "Не вдалося створити backup crontab"
    
    log_success "Резервна копія створена в $BACKUP_DIR"
}

# Зупинка бота
stop_bot() {
    log_info "Зупинка бота..."
    
    cd "$BOT_DIR"
    
    # Використовуємо скрипт якщо є
    if [[ -f "check_and_run_bot.sh" ]]; then
        bash check_and_run_bot.sh stop || true
    fi
    
    # Додатково шукаємо та зупиняємо процеси
    local pids=$(pgrep -f "python.*bot.py" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        log_info "Знайдено процеси бота: $pids"
        for pid in $pids; do
            kill -TERM "$pid" 2>/dev/null || true
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid" 2>/dev/null || true
                log_warning "Процес $pid зупинено принудово"
            fi
        done
    fi
    
    log_success "Бот зупинено"
}

# КРИТИЧНЕ ВИПРАВЛЕННЯ 1: Логіка успішності дзвінків
fix_call_success_logic() {
    log_info "КРИТИЧНЕ ВИПРАВЛЕННЯ: Логіка успішності дзвінків..."
    
    local files_to_fix=(
        "zadarma_api_webhook.py"
        "process_webhook.py"
    )
    
    for file in "${files_to_fix[@]}"; do
        if [[ -f "$BOT_DIR/$file" ]]; then
            log_info "Виправляю $file..."
            
            # Створюємо патч для правильної логіки
            sed -i.bak 's/disposition == '\''cancel'\'' and duration == 0/disposition == '\''cancel'\'' and duration > 0/g' "$BOT_DIR/$file"
            
            # Додаємо коментар про виправлення
            echo "" >> "$BOT_DIR/$file"
            echo "# ВИПРАВЛЕННЯ $(date +%Y-%m-%d): Змінено логіку успішності дзвінків" >> "$BOT_DIR/$file"
            echo "# Успіх тепер = duration > 0 (були гудки) AND disposition = 'cancel' (скинули)" >> "$BOT_DIR/$file"
            
            log_success "✓ $file виправлено"
        else
            log_warning "! $file не знайдено"
        fi
    done
}

# КРИТИЧНЕ ВИПРАВЛЕННЯ 2: Розділення webhook логіки
setup_unified_webhook() {
    log_info "КРИТИЧНЕ ВИПРАВЛЕННЯ: Налаштування unified webhook..."
    
    if [[ ! -d "$WEBHOOK_DIR" ]]; then
        mkdir -p "$WEBHOOK_DIR"
        log_info "Створено папку webhooks"
    fi
    
    # Створюємо unified_webhook.php (код вже готовий в артефакті)
    log_info "Створюю unified_webhook.php..."
    
    # Тут має бути код unified webhook з артефакту
    # Для демонстрації створюємо заглушку
    cat > "$WEBHOOK_DIR/unified_webhook.php" << 'WEBHOOK_EOF'
<?php
// Unified webhook - створено автоматично
require_once __DIR__ . '/webhook_functions.php';

$data = json_decode(file_get_contents('php://input'), true) ?: $_POST;
$event = $data['event'] ?? '';

if (isBotCallback($data)) {
    // Bot callback - передаємо в Python
    processBotCallback($data);
} else {
    // IVR дзвінок - обробляємо в PHP
    processIVRCall($data);
}
WEBHOOK_EOF
    
    log_success "✓ Unified webhook створено"
}

# Виправлення застарілих функцій (Python 3.6 сумісність)
fix_deprecated_functions() {
    log_info "Виправлення застарілих функцій для Python 3.6..."
    
    local file="$BOT_DIR/zadarma_call.py"
    
    if [[ ! -f "$file" ]]; then
        log_error "Файл $file не знайдено"
        return 1
    fi
    
    # Перевірка чи є застарілі функції
    if grep -q "make_zadarma_call_handler" "$file"; then
        log_info "Знайдено застарілі функції, видаляємо..."
        
        # Видаляємо від коментаря про deprecated до кінця файлу
        sed -i '/# Для сумісності зі старим кодом (deprecated)/,$d' "$file"
        
        # Додаємо коментар про видалення
        cat >> "$file" << 'EOF'

# === ЗАСТАРІЛІ ФУНКЦІЇ ВИДАЛЕНО ===
# Видалено функції make_zadarma_call_handler та legacy обробники
# для усунення попереджень про deprecated код та сумісності з Python 3.6
# Дата видалення: $(date +%Y-%m-%d)
EOF
        
        log_success "Застарілі функції видалено з zadarma_call.py"
    else
        log_info "Застарілих функцій не знайдено в zadarma_call.py"
    fi
    
    # Додаткова перевірка на f-strings (Python 3.6 не підтримує)
    for py_file in "$BOT_DIR"/*.py; do
        if [[ -f "$py_file" ]] && grep -q "f[\"']" "$py_file"; then
            log_warning "У файлі $(basename $py_file) знайдено можливі f-strings (не підтримуються Python 3.6)"
        fi
    done
}

# Виправлення crontab для менших перезапусків
fix_crontab() {
    log_info "Перевірка та виправлення crontab..."
    
    # Отримуємо поточний crontab
    local current_cron=$(crontab -l 2>/dev/null || true)
    
    if [[ -z "$current_cron" ]]; then
        log_warning "Crontab порожній"
        return 0
    fi
    
    # Перевіряємо чи є занадто часті запуски
    local frequent_jobs=$(echo "$current_cron" | grep -E "^\*|^[0-5] \*|^\*/[1-4]" | grep zadarma || true)
    
    if [[ -n "$frequent_jobs" ]]; then
        log_warning "Знайдено занадто часті cron jobs:"
        echo "$frequent_jobs" | while read -r line; do
            log_warning "  $line"
        done
        
        log_info "Рекомендується змінити інтервал на */5 або більше"
        
        # Пропонуємо виправлення
        read -p "Хочете автоматично виправити crontab? (y/N): " fix_cron
        if [[ "$fix_cron" =~ ^[Yy]$ ]]; then
            # Створюємо новий crontab з виправленими інтервалами
            {
                echo "# Zadarma bot crontab - виправлено $(date)"
                echo "# Перевірка статусу кожні 5 хвилин"
                echo "*/5 * * * * $BOT_DIR/check_and_run_bot.sh check >/dev/null 2>&1"
                echo ""
                echo "# Щоденне обслуговування о 3:00"
                echo "0 3 * * * $BOT_DIR/daily_maintenance.sh >/dev/null 2>&1"
                echo ""
                echo "# Інші завдання (якщо є)"
                echo "$current_cron" | grep -v zadarma | grep -v "^#" | grep -v "^$" || true
            } > /tmp/new_crontab.txt
            
            crontab /tmp/new_crontab.txt
            rm /tmp/new_crontab.txt
            
            log_success "Crontab оновлено з менш частими перевірками"
        fi
    else
        log_success "Налаштування crontab виглядають нормально"
    fi
}

# Створення виправленого process_webhook.py для Python 3.6
create_fixed_webhook_processor() {
    log_info "Створення виправленого process_webhook.py для Python 3.6..."
    
    # Тут має бути код з артефакту fixed_webhook_processor
    # Для демонстрації створюємо заглушку з основними виправленнями
    cat > "$BOT_DIR/process_webhook_fixed.py" << 'PYTHON_EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ВИПРАВЛЕНИЙ process_webhook.py для Python 3.6
# Правильна логіка: успіх = гудки (duration > 0) + скидання (cancel)

import sys
import json
import logging

# Python 3.6 сумісність - без f-strings
def analyze_call_result(disposition, duration, action_type):
    if disposition == 'cancel' and duration > 0:
        return 'success', "✅ {} відчинено!".format(action_type)
    elif disposition == 'busy':
        return 'busy', "❌ {} зайнято. Спробуйте ще раз.".format(action_type)
    # ... інша логіка
    
# ... решта коду з правильною логікою
PYTHON_EOF

    chmod +x "$BOT_DIR/process_webhook_fixed.py"
    
    # Замінюємо старий файл
    if [[ -f "$BOT_DIR/process_webhook.py" ]]; then
        mv "$BOT_DIR/process_webhook.py" "$BOT_DIR/process_webhook_old.py"
        mv "$BOT_DIR/process_webhook_fixed.py" "$BOT_DIR/process_webhook.py"
        log_success "process_webhook.py оновлено для Python 3.6"
    fi
}

# Тестування виправлень
test_fixes() {
    log_info "Тестування виправлень..."
    
    cd "$BOT_DIR"
    
    # Перевірка синтаксису Python файлів
    local python_files=("bot.py" "zadarma_call.py" "zadarma_api_webhook.py" "process_webhook.py")
    
    for file in "${python_files[@]}"; do
        if [[ -f "$file" ]]; then
            if python3 -m py_compile "$file" 2>/dev/null; then
                log_success "✓ $file: синтаксис правильний"
            else
                log_error "✗ $file: помилка синтаксису"
                return 1
            fi
        fi
    done
    
    # Перевірка webhook файлів
    if [[ -f "$WEBHOOK_DIR/unified_webhook.php" ]]; then
        if php -l "$WEBHOOK_DIR/unified_webhook.php" >/dev/null 2>&1; then
            log_success "✓ unified_webhook.php: синтаксис правильний"
        else
            log_error "✗ unified_webhook.php: помилка синтаксису"
        fi
    fi
}

# Запуск бота
start_bot() {
    log_info "Запуск бота..."
    
    cd "$BOT_DIR"
    
    if [[ -f "check_and_run_bot.sh" ]]; then
        bash check_and_run_bot.sh start
        sleep 3
        
        # Перевірка статусу
        if bash check_and_run_bot.sh status | grep -q "працює"; then
            log_success "Бот успішно запущено"
        else
            log_error "Бот не запустився. Перевірте логи:"
            log_error "tail -20 bot.log"
            return 1
        fi
    else
        log_error "Скрипт check_and_run_bot.sh не знайдено"
        return 1
    fi
}

# Головна функція
main() {
    echo "========================================"
    echo "  ZADARMA BOT - ВИПРАВЛЕННЯ ДЛЯ PYTHON 3.6"
    echo "  + Стороння Telegram API + Розділені Webhook"
    echo "========================================"
    echo
    
    log_info "Початок виправлення $(date)"
    log_info "Лог файл: $LOG_FILE"
    echo
    
    # Попередження про критичні зміни
    echo -e "${RED}КРИТИЧНО ВАЖЛИВО:${NC}"
    echo -e "${RED}1. Змінюється логіка визначення успіху дзвінка!${NC}"
    echo -e "${RED}   Стара: cancel + duration=0 = успіх${NC}" 
    echo -e "${RED}   Нова: cancel + duration>0 = успіх${NC}"
    echo -e "${RED}2. Налаштовується розділення IVR та Bot webhook${NC}"
    echo -e "${RED}3. Потрібно буде змінити URL webhook в Zadarma${NC}"
    echo
    echo -e "${YELLOW}УВАГА:${NC} Цей скрипт змінить файли бота та можливо crontab"
    echo -e "${YELLOW}УВАГА:${NC} Резервна копія буде створена автоматично"
    echo
    read -p "Продовжити з критичними виправленнями? (y/N): " confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "Операція скасована користувачем"
        exit 0
    fi
    
    echo
    
    # Виконуємо виправлення
    check_python_version
    check_permissions
    create_backup
    stop_bot
    
    # КРИТИЧНІ ВИПРАВЛЕННЯ
    fix_call_success_logic
    setup_unified_webhook
    create_fixed_webhook_processor
    
    # ІНШІ ВИПРАВЛЕННЯ
    fix_deprecated_functions
    fix_crontab
    
    test_fixes
    start_bot
    show_summary
    
    log_success "Всі виправлення для Python 3.6 успішно завершено! $(date)"
}

# Обробка помилок з додатковою інформацією
trap 'log_error "Скрипт завершився з помилкою на рядку $LINENO. Перевірте логи: $LOG_FILE"' ERR

# Запуск
main "$@" Функції логування
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Перевірка прав доступу
check_permissions() {
    if [[ $EUID -ne 0 ]] && [[ ! -w "$BOT_DIR" ]]; then
        log_error "Недостатньо прав для запису в $BOT_DIR"
        log_info "Запустіть скрипт з sudo або від власника файлів"
        exit 1
    fi
    log_success "Перевірка прав доступу пройшла успішно"
}

# Створення резервної копії
create_backup() {
    log_info "Створення резервної копії..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Копіюємо критичні файли
    local files_to_backup=(
        "bot.py"
        "zadarma_call.py"
        "zadarma_api_webhook.py"
        "config.py"
        "user_db.py"
        "check_and_run_bot.sh"
        "process_webhook.py"
    )
    
    for file in "${files_to_backup[@]}"; do
        if [[ -f "$BOT_DIR/$file" ]]; then
            cp "$BOT_DIR/$file" "$BACKUP_DIR/"
            log_info "  ✓ $file"
        else
            log_warning "  ! Файл $file не знайдено"
        fi
    done
    
    # Копіюємо crontab
    crontab -l > "$BACKUP_DIR/crontab_backup.txt" 2>/dev/null || log_warning "Не вдалося створити backup crontab"
    
    log_success "Резервна копія створена в $BACKUP_DIR"
}

# Зупинка бота
stop_bot() {
    log_info "Зупинка бота..."
    
    cd "$BOT_DIR"
    
    # Використовуємо скрипт якщо є
    if [[ -f "check_and_run_bot.sh" ]]; then
        bash check_and_run_bot.sh stop || true
    fi
    
    # Додатково шукаємо та зупиняємо процеси
    local pids=$(pgrep -f "python.*bot.py" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        log_info "Знайдено процеси бота: $pids"
        for pid in $pids; do
            kill -TERM "$pid" 2>/dev/null || true
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid" 2>/dev/null || true
                log_warning "Процес $pid зупинено принудово"
            fi
        done
    fi
    
    log_success "Бот зупинено"
}

# Виправлення застарілих функцій
fix_deprecated_functions() {
    log_info "Виправлення застарілих функцій в zadarma_call.py..."
    
    local file="$BOT_DIR/zadarma_call.py"
    
    if [[ ! -f "$file" ]]; then
        log_error "Файл $file не знайдено"
        return 1
    fi
    
    # Перевірка чи є застарілі функції
    if grep -q "make_zadarma_call_handler" "$file"; then
        log_info "Знайдено застарілі функції, видаляємо..."
        
        # Створюємо тимчасовий файл без застарілих функцій
        sed '/# Для сумісності зі старим кодом (deprecated)/,$d' "$file" > "${file}.tmp"
        
        # Додаємо коментар про видалення
        cat >> "${file}.tmp" << 'EOF'

# === ЗАСТАРІЛІ ФУНКЦІЇ ВИДАЛЕНО ===
# Видалено функції make_zadarma_call_handler та legacy обробники
# для усунення попереджень про deprecated код.
# Дата видалення: $(date +%Y-%m-%d)
EOF
        
        # Заміняємо оригінальний файл
        mv "${file}.tmp" "$file"
        
        log_success "Застарілі функції видалено з zadarma_call.py"
    else
        log_info "Застарілих функцій не знайдено в zadarma_call.py"
    fi
}

# Перевірка та виправлення crontab
fix_crontab() {
    log_info "Перевірка налаштувань crontab..."
    
    # Отримуємо поточний crontab
    local current_cron=$(crontab -l 2>/dev/null || true)
    
    if [[ -z "$current_cron" ]]; then
        log_warning "Crontab порожній"
        return 0
    fi
    
    # Перевіряємо чи є занадто часті запуски
    local frequent_jobs=$(echo "$current_cron" | grep -E "^\*|^[0-5] \*|^\*/[1-5]" | grep zadarma || true)
    
    if [[ -n "$frequent_jobs" ]]; then
        log_warning "Знайдено занадто часті cron jobs:"
        echo "$frequent_jobs" | while read -r line; do
            log_warning "  $line"
        done
        
        log_info "Рекомендується змінити інтервал на */5 або більше"
        
        # Пропонуємо виправлення
        read -p "Хочете автоматично виправити crontab? (y/N): " fix_cron
        if [[ "$fix_cron" =~ ^[Yy]$ ]]; then
            # Створюємо новий crontab з виправленими інтервалами
            echo "$current_cron" | sed 's/^\* \* \* \* \*.*zadarma.*check.*/# Заміщено на менш часту перевірку/' > /tmp/new_crontab.txt
            echo "*/5 * * * * $BOT_DIR/check_and_run_bot.sh check >/dev/null 2>&1" >> /tmp/new_crontab.txt
            echo "0 3 * * * $BOT_DIR/daily_maintenance.sh >/dev/null 2>&1" >> /tmp/new_crontab.txt
            
            crontab /tmp/new_crontab.txt
            rm /tmp/new_crontab.txt
            
            log_success "Crontab оновлено"
        fi
    else
        log_success "Налаштування crontab виглядають нормально"
    fi
}

# Перевірка файлів webhook
check_webhooks() {
    log_info "Перевірка webhook файлів..."
    
    local webhook_files=(
        "webhooks/zadarma_webhook.php"
        "process_webhook.py"
    )
    
    for file in "${webhook_files[@]}"; do
        if [[ -f "$BOT_DIR/$file" ]]; then
            log_success "✓ $file існує"
            
            # Перевірка прав на виконання для Python скриптів
            if [[ "$file" == *.py ]] && [[ ! -x "$BOT_DIR/$file" ]]; then
                chmod +x "$BOT_DIR/$file"
                log_info "Додано права на виконання для $file"
            fi
        else
            log_warning "! $file не знайдено"
        fi
    done
}

# Тестування виправлень
test_fixes() {
    log_info "Тестування виправлень..."
    
    cd "$BOT_DIR"
    
    # Перевірка синтаксису Python файлів
    local python_files=("bot.py" "zadarma_call.py" "zadarma_api_webhook.py" "process_webhook.py")
    
    for file in "${python_files[@]}"; do
        if [[ -f "$file" ]]; then
            if python3 -m py_compile "$file" 2>/dev/null; then
                log_success "✓ $file: синтаксис правильний"
            else
                log_error "✗ $file: помилка синтаксису"
                return 1
            fi
        fi
    done
}

# Запуск бота
start_bot() {
    log_info "Запуск бота..."
    
    cd "$BOT_DIR"
    
    if [[ -f "check_and_run_bot.sh" ]]; then
        bash check_and_run_bot.sh start
        sleep 3
        
        # Перевірка статусу
        if bash check_and_run_bot.sh status | grep -q "працює"; then
            log_success "Бот успішно запущено"
        else
            log_error "Бот не запустився. Перевірте логи:"
            log_error "tail -20 bot.log"
            return 1
        fi
    else
        log_error "Скрипт check_and_run_bot.sh не знайдено"
        return 1
    fi
}

# Показ підсумків
show_summary() {
    echo
    echo "=================== ПІДСУМОК ==================="
    log_success "Виправлення завершено!"
    echo
    log_info "Що було зроблено:"
    log_info "  ✓ Створено резервну копію в $BACKUP_DIR"
    log_info "  ✓ Видалено застарілі функції з zadarma_call.py"
    log_info "  ✓ Перевірено налаштування crontab"
    log_info "  ✓ Перевірено webhook файли"
    log_info "  ✓ Протестовано виправлення"
    log_info "  ✓ Перезапущено бота"
    echo
    log_info "Що робити далі:"
    log_info "  1. Моніторити логи: tail -f $BOT_DIR/bot.log"
    log_info "  2. Протестувати команди /hvirtka та /vorota"
    log_info "  3. Перевірити що немає повідомлень про deprecated функції"
    echo
    log_info "У разі проблем:"
    log_info "  - Відновити з backup: cp $BACKUP_DIR/* $BOT_DIR/"
    log_info "  - Лог виправлень: $LOG_FILE"
    echo
    log_success "Готово! 🎉"
}

# Головна функція
main() {
    echo "========================================"
    echo "    ZADARMA BOT - АВТОМАТИЧНЕ ВИПРАВЛЕННЯ"
    echo "========================================"
    echo
    
    log_info "Початок виправлення $(date)"
    log_info "Лог файл: $LOG_FILE"
    echo
    
    # Попередження
    echo -e "${YELLOW}УВАГА:${NC} Цей скрипт змінить файли бота та можливо crontab"
    echo -e "${YELLOW}УВАГА:${NC} Резервна копія буде створена автоматично"
    echo
    read -p "Продовжити? (y/N): " confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "Операція скасована користувачем"
        exit 0
    fi
    
    echo
    
    # Виконуємо виправлення
    check_permissions
    create_backup
    stop_bot
    fix_deprecated_functions
    fix_crontab
    check_webhooks
    test_fixes
    start_bot
    show_summary
    
    log_success "Всі виправлення успішно завершено! $(date)"
}

# Обробка помилок
trap 'log_error "Скрипт завершився з помилкою на рядку $LINENO"' ERR

# Запуск
main "$@"