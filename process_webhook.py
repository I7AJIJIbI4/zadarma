#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
process_webhook.py - Обробник webhook-ів для інтеграції з телеграм ботом
Викликається з PHP webhook-а для обробки подій Zadarma
"""

import sys
import json
import logging
import os

# Додаємо шлях до нашого проекту
sys.path.append('/home/gomoncli/zadarma')

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/gomoncli/zadarma/webhook_processor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('webhook_processor')

def main():
    """Головна функція обробки webhook"""
    try:
        # Отримуємо JSON данні з аргументів командного рядка
        if len(sys.argv) < 2:
            logger.error("❌ Не передано JSON данні")
            sys.exit(1)
        
        json_data = sys.argv[1]
        logger.info(f"📥 Отримано данні: {json_data}")
        
        # Парсимо JSON
        try:
            webhook_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Помилка парсингу JSON: {e}")
            sys.exit(1)
        
        # Імпортуємо наш модуль webhook обробки
        try:
            from zadarma_api_webhook import process_webhook_call_status
        except ImportError as e:
            logger.error(f"❌ Помилка імпорту zadarma_api_webhook: {e}")
            # Fallback - пробуємо імпортувати зі старого модуля
            try:
                from zadarma_api import process_webhook_call_status
            except ImportError:
                logger.error("❌ Не вдалося імпортувати process_webhook_call_status")
                sys.exit(1)
        
        # Обробляємо webhook
        result = process_webhook_call_status(webhook_data)
        
        if result['success']:
            logger.info(f"✅ Webhook успішно оброблено: {result.get('message', '')}")
            print(json.dumps(result))  # Виводимо результат для PHP
            sys.exit(0)
        else:
            logger.error(f"❌ Помилка обробки webhook: {result.get('message', '')}")
            print(json.dumps(result))
            sys.exit(1)
        
    except Exception as e:
        logger.exception(f"❌ Критична помилка в process_webhook: {e}")
        error_result = {"success": False, "message": str(e)}
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()
