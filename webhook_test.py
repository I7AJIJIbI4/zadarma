#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
webhook_test.py - Перевірка налаштувань webhook в Zadarma API
"""

import sys
import json
import logging
import requests
import hashlib
import base64

# Додаємо шлях до проекту
sys.path.append('/home/gomoncli/zadarma')

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('webhook_test')

def test_webhook_settings():
    """Перевіряє поточні налаштування webhook в Zadarma"""
    try:
        from config import ZADARMA_USER_KEY, ZADARMA_SECRET_KEY
        
        # Zadarma API параметри
        method = 'GET'
        api_method = '/v1/info/price/'
        params = 'format=json'
        
        # Створюємо підпис
        sign = base64.b64encode(
            hashlib.md5(f"{method}{api_method}{params}{ZADARMA_SECRET_KEY}".encode()).digest()
        ).decode()
        
        headers = {
            'Authorization': f"{ZADARMA_USER_KEY}:{sign}",
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Тестуємо з'єднання
        url = f"https://api.zadarma.com{api_method}?{params}"
        logger.info(f"🌐 Тестуємо з'єднання з Zadarma API...")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ З'єднання з Zadarma API працює")
            return True
        else:
            logger.error(f"❌ Помилка з'єднання: {response.status_code}")
            logger.error(f"❌ Відповідь: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Помилка тестування API: {e}")
        return False

def check_webhook_logs():
    """Перевіряє логи webhook"""
    webhook_log_paths = [
        '/home/gomoncli/zadarma/telegram_webhook.log',
        '/home/gomoncli/zadarma/webhook_processor.log',
        '/home/gomoncli/zadarma/ivr_webhook.log'
    ]
    
    logger.info("📋 Перевіряємо логи webhook...")
    
    for log_path in webhook_log_paths:
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_lines = lines[-10:] if len(lines) > 10 else lines
                
                logger.info(f"📁 {log_path} - останні записи:")
                for line in recent_lines:
                    logger.info(f"  {line.strip()}")
                    
        except FileNotFoundError:
            logger.warning(f"⚠️ Файл логу не знайдено: {log_path}")
        except Exception as e:
            logger.error(f"❌ Помилка читання логу {log_path}: {e}")

def test_webhook_url():
    """Тестує доступність webhook URL"""
    webhook_urls = [
        'https://gomoncli.beget.tech/telegram_webhook.php',
        'http://gomoncli.beget.tech/telegram_webhook.php'
    ]
    
    logger.info("🌐 Тестуємо доступність webhook URL...")
    
    for url in webhook_urls:
        try:
            logger.info(f"🔗 Тестуємо: {url}")
            
            # Тестуємо GET запит
            response = requests.get(url, timeout=10)
            logger.info(f"  GET статус: {response.status_code}")
            
            # Тестуємо POST запит з тестовими даними
            test_data = {
                'event': 'TEST',
                'caller_id': '380733103110',
                'pbx_call_id': 'test123'
            }
            
            response = requests.post(url, json=test_data, timeout=10)
            logger.info(f"  POST статус: {response.status_code}")
            logger.info(f"  POST відповідь: {response.text[:200]}")
            
        except Exception as e:
            logger.error(f"❌ Помилка тестування {url}: {e}")

def simulate_webhook_call():
    """Симулює webhook виклик для тестування"""
    logger.info("🧪 Симулюємо webhook виклик...")
    
    # Тестові дані як від Zadarma
    test_webhook_data = {
        'event': 'NOTIFY_END',
        'caller_id': '380733103110',
        'destination': '0637442017',
        'pbx_call_id': 'test_' + str(int(time.time())),
        'disposition': 'cancel',
        'duration': '0',
        'call_start': str(int(time.time()))
    }
    
    logger.info(f"📤 Тестові дані: {json.dumps(test_webhook_data, ensure_ascii=False)}")
    
    try:
        # Імпортуємо функцію обробки
        from process_webhook import main as process_webhook_main
        
        # Симулюємо виклик
        import sys
        original_argv = sys.argv.copy()
        
        sys.argv = ['process_webhook.py', json.dumps(test_webhook_data)]
        
        try:
            process_webhook_main()
            logger.info("✅ Симуляція webhook успішна")
        finally:
            sys.argv = original_argv
            
    except Exception as e:
        logger.error(f"❌ Помилка симуляції webhook: {e}")

def check_zadarma_settings():
    """Перевіряє налаштування в особистому кабінеті Zadarma"""
    logger.info("📋 Інструкції для перевірки налаштувань Zadarma:")
    logger.info("")
    logger.info("1. Увійдіть в особистий кабінет Zadarma")
    logger.info("2. Перейдіть в розділ 'API' -> 'Webhook'")
    logger.info("3. Перевірте URL webhook:")
    logger.info("   https://gomoncli.beget.tech/telegram_webhook.php")
    logger.info("")
    logger.info("4. Перевірте, що увімкнені події:")
    logger.info("   ✅ NOTIFY_START")
    logger.info("   ✅ NOTIFY_END") 
    logger.info("   ✅ NOTIFY_INTERNAL")
    logger.info("")
    logger.info("5. Якщо webhook не налаштований - додайте його!")

def main():
    """Головна функція тестування"""
    logger.info("🔍 Початок діагностики webhook...")
    logger.info("=" * 50)
    
    # 1. Тестуємо API з'єднання
    logger.info("1️⃣ Тестування API з'єднання...")
    if test_webhook_settings():
        logger.info("✅ API з'єднання працює")
    else:
        logger.error("❌ Проблеми з API з'єднанням")
    
    logger.info("=" * 50)
    
    # 2. Перевіряємо логи
    logger.info("2️⃣ Перевірка логів...")
    check_webhook_logs()
    
    logger.info("=" * 50)
    
    # 3. Тестуємо webhook URL
    logger.info("3️⃣ Тестування webhook URL...")
    test_webhook_url()
    
    logger.info("=" * 50)
    
    # 4. Симулюємо webhook
    logger.info("4️⃣ Симуляція webhook...")
    simulate_webhook_call()
    
    logger.info("=" * 50)
    
    # 5. Інструкції
    logger.info("5️⃣ Інструкції налаштування...")
    check_zadarma_settings()
    
    logger.info("=" * 50)
    logger.info("🏁 Діагностика завершена")

if __name__ == "__main__":
    import time
    main()