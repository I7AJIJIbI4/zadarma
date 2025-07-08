#!/bin/bash

LOCKFILE=/tmp/zadarma_bot.lock
exec 200>"$LOCKFILE"

flock -n 200 || {
    echo "Zadarma бот вже запущений"
    exit 1
}

# Якщо немає virtualenv — пропусти цей рядок
# source /home/gomoncli/venv/bin/activate

# Запуск бота через системний python3 (бо віртуальне оточення не працює)
python3 /home/gomoncli/zadarma/bot.py
