#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ВИПРАВЛЕНИЙ process_webhook.py для Python 3.6
# ✅ КРИТИЧНА ВИПРАВЛЕНА ЛОГІКА: успіх = duration > 0 + cancel  
# ✅ Без f-strings для сумісності з Python 3.6
# ✅ Видалено застарілі функції

import sys
import json
import sqlite3
import time
import logging
import requests
import traceback
from datetime import datetime

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/webhook_processor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def load_config():
    """Завантажує конфігурацію"""
    try:
        with open('config.py', 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        import re
        
        # Витягуємо необхідні конфігурації
        token_match = re.search(r'TELEGRAM_TOKEN\s*=\s*[\'"]([^\'"]+)[\'"]', config_content)
        hvirtka_match = re.search(r'HVIRTKA_NUMBER\s*=\s*[\'"]([^\'"]+)[\'"]', config_content)
        vorota_match = re.search(r'VOROTA_NUMBER\s*=\s*[\'"]([^\'"]+)[\'"]', config_content)
        
        config = {}
        if token_match:
            config['TELEGRAM_TOKEN'] = token_match.group(1)
        if hvirtka_match:
            config['HVIRTKA_NUMBER'] = hvirtka_match.group(1)
        if vorota_match:
            config['VOROTA_NUMBER'] = vorota_match.group(1)
            
        return config
        
    except Exception as e:
        logger.error("Failed to load config: {}".format(e))
        return {}

def send_telegram_message(chat_id, message, config):
    """Відправляє повідомлення в Telegram"""
    try:
        if 'TELEGRAM_TOKEN' not in config:
            logger.error("TELEGRAM_TOKEN not found in config")
            return False
            
        token = config['TELEGRAM_TOKEN']
        url = "https://api.telegram.org/bot{}/sendMessage".format(token)
        
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            logger.info("Message sent successfully to chat {}".format(chat_id))
            return True
        else:
            logger.error("Failed to send message: {} - {}".format(response.status_code, response.text))
            return False
            
    except Exception as e:
        logger.error("Telegram error: {}".format(e))
        return False

def find_pending_call(target_number, time_window=120):
    """Знаходить очікуючий дзвінок в базі даних"""
    try:
        conn = sqlite3.connect('call_tracking.db')
        cursor = conn.cursor()
        
        current_time = int(time.time())
        time_start = current_time - time_window
        
        # Шукаємо останній дзвінок зі статусом api_success
        cursor.execute('''
            SELECT call_id, user_id, chat_id, action_type, target_number, start_time, status
            FROM call_tracking 
            WHERE target_number = ? AND start_time > ? AND status = 'api_success'
            ORDER BY start_time DESC LIMIT 1
        ''', (target_number, time_start))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'call_id': result[0],
                'user_id': result[1], 
                'chat_id': result[2],
                'action_type': result[3],
                'target_number': result[4],
                'start_time': result[5],
                'status': result[6]
            }
        return None
        
    except Exception as e:
        logger.error("Database error: {}".format(e))
        return None

def update_call_status(call_id, status):
    """Оновлює статус дзвінка в базі даних"""
    try:
        conn = sqlite3.connect('call_tracking.db')
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE call_tracking SET status = ? WHERE call_id = ?',
            (status, call_id)
        )
        
        conn.commit()
        conn.close()
        
        logger.info("Call {} status updated to {}".format(call_id, status))
        return True
        
    except Exception as e:
        logger.error("Failed to update call status: {}".format(e))
        return False

def analyze_call_result(disposition, duration, action_type):
    """
    ✅ ВИПРАВЛЕНА КРИТИЧНА ЛОГІКА УСПІХУ
    
    Правильна логіка для систем контролю доступу:
    - SUCCESS: були гудки (duration > 0) + скинули (cancel) = пристрій відповів і відкрився
    - BUSY: зайнято 
    - NO_ANSWER: немає відповіді (duration = 0)
    """
    
    action_name = action_type.lower()
    if action_name == 'hvirtka':
        device_name = 'хвіртка'
    elif action_name == 'vorota':
        device_name = 'ворота'
    else:
        device_name = action_name
    
    # ✅ КРИТИЧНО ВАЖЛИВА ЗМІНА: успіх = duration > 0 (були гудки) + cancel (скинули)
    if disposition == 'cancel' and duration > 0:
        return 'success', "✅ {} відчинено!".format(device_name.capitalize())
        
    elif disposition == 'busy':
        return 'busy', "❌ Номер {} зайнятий. Спробуйте ще раз.".format(device_name)
        
    elif disposition in ['no-answer', 'noanswer', 'cancel'] and duration == 0:
        return 'no_answer', "❌ Номер {} не відповідає.".format(device_name)
        
    elif disposition == 'answered':
        return 'answered', "📞 З'єднання з {} встановлено, але статус невідомий.".format(device_name)
        
    else:
        return 'failed', "❌ Не вдалося відкрити {}. Статус: {}".format(device_name, disposition)

def determine_action_type(called_did, config):
    """Визначає тип дії на основі номера, що викликається"""
    
    hvirtka_number = config.get('HVIRTKA_NUMBER', '0637442017')
    vorota_number = config.get('VOROTA_NUMBER', '0930063585')
    
    # Прибираємо префікси та перевіряємо
    called_clean = called_did.replace('+38', '').replace('+', '').lstrip('0')
    hvirtka_clean = hvirtka_number.replace('+38', '').replace('+', '').lstrip('0')
    vorota_clean = vorota_number.replace('+38', '').replace('+', '').lstrip('0')
    
    if hvirtka_clean in called_clean or hvirtka_number in called_did:
        return 'hvirtka', hvirtka_number
    elif vorota_clean in called_clean or vorota_number in called_did:
        return 'vorota', vorota_number
    else:
        logger.warning("Unknown called_did: {}".format(called_did))
        return None, None

def process_webhook_data(webhook_data):
    """Основна функція обробки webhook даних"""
    
    logger.info("Processing webhook data: {}".format(webhook_data))
    
    # Завантажуємо конфігурацію
    config = load_config()
    
    # Перевіряємо обов'язкові поля
    event = webhook_data.get('event', '')
    caller_id = webhook_data.get('caller_id', '')
    called_did = webhook_data.get('called_did', '')
    disposition = webhook_data.get('disposition', '')
    duration = int(webhook_data.get('duration', 0))
    
    logger.info("Event: {}, Caller: {}, Called: {}, Disposition: {}, Duration: {}".format(
        event, caller_id, called_did, disposition, duration))
    
    # Обробляємо тільки завершення дзвінків
    if event != 'NOTIFY_END':
        logger.info("Ignoring event type: {}".format(event))
        return {'status': 'ignored', 'reason': 'not_notify_end'}
    
    # Визначаємо тип дії
    action_type, target_number = determine_action_type(called_did, config)
    
    if not action_type:
        logger.warning("Cannot determine action type for called_did: {}".format(called_did))
        return {'status': 'error', 'reason': 'unknown_number'}
    
    logger.info("Detected action: {} for number: {}".format(action_type, target_number))
    
    # Шукаємо відповідний запит в базі даних
    call_data = find_pending_call(target_number)
    
    if not call_data:
        logger.warning("No pending call found for number: {}".format(target_number))
        return {'status': 'error', 'reason': 'call_not_found'}
    
    logger.info("Found call: {} for user: {}".format(call_data['call_id'], call_data['chat_id']))
    
    # Аналізуємо результат дзвінка
    result_status, message = analyze_call_result(disposition, duration, action_type)
    
    logger.info("Call result: {} - {}".format(result_status, message))
    
    # Відправляємо повідомлення користувачу
    success = send_telegram_message(call_data['chat_id'], message, config)
    
    if not success:
        logger.error("Failed to send Telegram message")
        return {'status': 'error', 'reason': 'telegram_failed'}
    
    # Оновлюємо статус в базі даних
    update_success = update_call_status(call_data['call_id'], result_status)
    
    if not update_success:
        logger.error("Failed to update call status in database")
    
    return {
        'status': 'success',
        'call_id': call_data['call_id'],
        'result_status': result_status,
        'message_sent': success,
        'db_updated': update_success
    }

def main():
    """Головна функція"""
    
    if len(sys.argv) < 2:
        logger.error("No webhook data provided")
        logger.error("Usage: python3 process_webhook.py '<json_data>'")
        sys.exit(1)
    
    try:
        # Парсимо JSON дані з аргументів командного рядка
        webhook_json = sys.argv[1]
        webhook_data = json.loads(webhook_json)
        
        # Обробляємо webhook
        result = process_webhook_data(webhook_data)
        
        logger.info("Processing result: {}".format(result))
        
        # Виводимо результат
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON data: {}".format(e))
        print(json.dumps({'status': 'error', 'reason': 'invalid_json', 'details': str(e)}))
        sys.exit(1)
        
    except Exception as e:
        logger.error("Unexpected error: {}".format(e))
        logger.error("Traceback: {}".format(traceback.format_exc()))
        print(json.dumps({'status': 'error', 'reason': 'unexpected_error', 'details': str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
