#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
process_webhook.py - Enhanced webhook processor with improved logic

Обробляє webhook запити від Zadarma API з покращеною логікою
визначення успішності дзвінків та правильним логуванням.
"""

import sys
import json
import logging
import sqlite3
from datetime import datetime
import os

# Налаштування логування
log_file = '/home/gomoncli/zadarma/webhook_processor.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Константи
DB_PATH = '/home/gomoncli/zadarma/call_tracking.db'

def init_call_tracking_db():
    """Ініціалізує базу даних для відстеження дзвінків"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT UNIQUE,
                caller_id TEXT,
                called_number TEXT,
                event TEXT,
                duration INTEGER,
                disposition TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_successful BOOLEAN,
                webhook_data TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ База даних call_tracking ініціалізована")
        return True
        
    except Exception as e:
        logger.error("❌ Помилка ініціалізації бази даних: {}".format(e))
        return False

def is_call_successful(webhook_data):
    """
    Покращена логіка визначення успішності дзвінка
    
    Дзвінок вважається успішним якщо:
    1. Duration > 0 (була розмова)
    2. Disposition = 'ANSWERED' 
    3. Event = 'NOTIFY_END' з позитивною тривалістю
    """
    try:
        # Перевірка тривалості
        duration = int(webhook_data.get('duration', 0))
        if duration > 0:
            logger.info("✅ Дзвінок успішний: duration = {}".format(duration))
            return True
        
        # Перевірка статусу
        disposition = webhook_data.get('disposition', '').upper()
        if disposition == 'ANSWERED':
            logger.info("✅ Дзвінок успішний: disposition = ANSWERED")
            return True
        
        # Для IVR дзвінків перевіряємо інші параметри
        event = webhook_data.get('event', '')
        if event == 'NOTIFY_END':
            # Якщо є будь-які ознаки взаємодії
            pbx_call_id = webhook_data.get('pbx_call_id')
            if pbx_call_id:
                logger.info("✅ Дзвінок успішний: pbx_call_id присутній")
                return True
        
        # Дзвінок неуспішний
        logger.info("❌ Дзвінок неуспішний: duration={}, disposition={}".format(duration, disposition))
        return False
        
    except Exception as e:
        logger.error("❌ Помилка при визначенні успішності дзвінка: {}".format(e))
        return False

def save_call_data(webhook_data):
    """Зберігає дані дзвінка в базу даних"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        call_id = webhook_data.get('call_id', webhook_data.get('pbx_call_id', ''))
        caller_id = webhook_data.get('caller_id', '')
        called_number = webhook_data.get('called_did', webhook_data.get('internal', ''))
        event = webhook_data.get('event', '')
        duration = int(webhook_data.get('duration', 0))
        disposition = webhook_data.get('disposition', '')
        is_successful = is_call_successful(webhook_data)
        
        cursor.execute('''
            INSERT OR REPLACE INTO calls 
            (call_id, caller_id, called_number, event, duration, disposition, is_successful, webhook_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (call_id, caller_id, called_number, event, duration, disposition, is_successful, json.dumps(webhook_data)))
        
        conn.commit()
        conn.close()
        
        logger.info("💾 Дані дзвінка збережено: {} -> {} ({} сек, успішний: {})".format(
            caller_id, called_number, duration, is_successful))
        return True
        
    except Exception as e:
        logger.error("❌ Помилка збереження дзвінка: {}".format(e))
        return False

def process_webhook_data(webhook_json):
    """Основна функція обробки webhook даних"""
    try:
        if not webhook_json:
            logger.error("❌ Порожні webhook дані")
            return False
            
        webhook_data = json.loads(webhook_json) if isinstance(webhook_json, str) else webhook_json
        
        # Логування отриманих даних
        event = webhook_data.get('event', 'UNKNOWN')
        caller = webhook_data.get('caller_id', 'N/A')
        called = webhook_data.get('called_did', webhook_data.get('internal', 'N/A'))
        
        logger.info("📞 Webhook обробка: event={}, caller={}, called={}".format(event, caller, called))
        
        # Ініціалізація БД якщо потрібно
        if not os.path.exists(DB_PATH):
            init_call_tracking_db()
        
        # Збереження даних
        save_call_data(webhook_data)
        
        # Додаткова обробка для специфічних подій
        if event == 'NOTIFY_START':
            logger.info("🟢 Дзвінок почався: {} -> {}".format(caller, called))
        elif event == 'NOTIFY_END':
            duration = webhook_data.get('duration', 0)
            success = is_call_successful(webhook_data)
            status = "успішний" if success else "неуспішний"
            logger.info("🔴 Дзвінок завершено: {} сек, {}".format(duration, status))
        
        return True
        
    except json.JSONDecodeError as e:
        logger.error("❌ Помилка парсинга JSON: {}".format(e))
        return False
    except Exception as e:
        logger.error("❌ Загальна помилка обробки webhook: {}".format(e))
        return False

def main():
    """Головна функція для запуску з командного рядка"""
    if len(sys.argv) < 2:
        logger.error("❌ Використання: python3 process_webhook.py '<json_data>'")
        sys.exit(1)
    
    webhook_json = sys.argv[1]
    
    logger.info("🚀 Запуск process_webhook.py")
    logger.info("📨 Отримані дані: {}".format(webhook_json[:200] + "..." if len(webhook_json) > 200 else webhook_json))
    
    success = process_webhook_data(webhook_json)
    
    if success:
        logger.info("✅ Webhook успішно оброблено")
        print("SUCCESS")
    else:
        logger.error("❌ Помилка обробки webhook")
        print("ERROR")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
