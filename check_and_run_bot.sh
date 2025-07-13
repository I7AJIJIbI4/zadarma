#!/bin/bash

# === Налаштування ===
LOCKFILE=/tmp/zadarma_bot.lock
BOT_DIR="/home/gomoncli/zadarma"
BOT_SCRIPT="bot.py"
LOGFILE="$BOT_DIR/bot_cron.log"
PYTHON_EXEC="/usr/bin/python3"  # Заміни на свій шлях, якщо інший

# === Блокування через flock ===
exec 200>"$LOCKFILE"
flock -n 200 || {
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Бот вже запущений (lock)" >> "$LOGFILE"
    exit 1
}

# === Перевірка процесу (додатково до flock) ===
if pgrep -f "$BOT_SCRIPT" > /dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Бот вже запущений (pgrep)" >> "$LOGFILE"
    exit 0
fi

# === (Опційно) Активація віртуального середовища ===
# source /home/gomoncli/venv/bin/activate

# === Запуск бота у фоновому режимі ===
echo "$(date '+%Y-%m-%d %H:%M:%S') — Запускаю бота..." >> "$LOGFILE"
cd "$BOT_DIR"
$PYTHON_EXEC "$BOT_SCRIPT" >> "$BOT_DIR/bot.log" 2>&1 &
