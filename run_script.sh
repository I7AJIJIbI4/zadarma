#!/bin/bash
cd /home/gomoncli/zadarma
source /home/gomoncli/venv/bin/activate  # якщо є virtualenv, інакше прибрати цей рядок
python3 bot.py >> bot.log 2>&1
