#!/bin/bash

echo "🔧 РОЗГОРТАННЯ ВИПРАВЛЕННЯ WEBHOOK"
echo "=================================="

PROJECT_DIR="/home/gomoncli/zadarma"
cd $PROJECT_DIR

# Кольори
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m' 
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📁 Робочий каталог: $PROJECT_DIR${NC}"

# 1. Створюємо резервну копію
echo -e "${YELLOW}1️⃣ Створюємо резервну копію...${NC}"
if [ -f "process_webhook.py" ]; then
    cp process_webhook.py process_webhook.py.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Резервна копія створена${NC}"
else
    echo -e "${YELLOW}⚠️ Поточний файл не знайдено${NC}"
fi

# 2. Замінюємо файл
echo -e "${YELLOW}2️⃣ Встановлюємо новий обробник...${NC}"

# Створюємо новий файл process_webhook.py з покращеним кодом
cat > process_webhook.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
process_webhook.py - ВИПРАВЛЕНИЙ обробник webhook-ів
Покращений алгоритм пошуку дзвінків через номер телефону та час
"""

import sys
import json
import logging
import os
import time
from datetime import datetime, timedelta

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

def normalize_phone_number(phone):
    """Нормалізує номер телефону для порівняння"""
    if not phone:
        return ""
    
    # Видаляємо всі символи крім цифр
    normalized = ''.join(filter(str.isdigit, str(phone)))
    
    # Видаляємо префікси
    if normalized.startswith('380'):
        normalized = normalized[3:]
    elif normalized.startswith('38'):
        normalized = normalized[2:]
    elif normalized.startswith('0'):
        normalized = normalized[1:]
    
    return normalized

def find_tracked_call(pbx_call_id, caller_id, call_tracker, time_window=300):
    """
    Покращений пошук відстежуваного дзвінка
    """
    logger.info(f"🔍 Розширений пошук дзвінка...")
    logger.info(f"   PBX ID: {pbx_call_id}")
    logger.info(f"   Caller ID: {caller_id}")
    
    # 1. Спочатку пробуємо знайти по PBX ID
    if pbx_call_id:
        call_data = call_tracker.get_call_by_pbx_id(pbx_call_id)
        if call_data:
            logger.info(f"✅ Знайдено по PBX ID: {pbx_call_id}")
            return call_data
        logger.info(f"❌ Не знайдено по PBX ID: {pbx_call_id}")
    
    # 2. Нормалізуємо номер з webhook
    normalized_caller = normalize_phone_number(caller_id)
    logger.info(f"🔢 Нормалізований номер: '{caller_id}' -> '{normalized_caller}'")
    
    # 3. Визначаємо цільові номери для пошуку
    target_numbers = []
    
    # Наші номери хвіртки та воріт
    hvirtka_variations = ['637442017', '0637442017', '380637442017']
    vorota_variations = ['930063585', '0930063585', '380930063585']
    
    # Якщо caller_id містить наш номер, додаємо його варіації
    if any(num in caller_id for num in ['637442017', '930063585']):
        if '637442017' in caller_id:
            target_numbers.extend(hvirtka_variations)
            logger.info("🚪 Визначено як дзвінок на хвіртку")
        elif '930063585' in caller_id:
            target_numbers.extend(vorota_variations)
            logger.info("🏠 Визначено як дзвінок на ворота")
    
    # 4. Шукаємо по цільових номерах з часовим вікном
    current_time = time.time()
    
    for target_number in target_numbers:
        logger.info(f"🔍 Пошук по номеру: {target_number}")
        
        # Пробуємо різні варіанти часового вікна
        for time_range in [60, 120, 300, 600]:  # 1, 2, 5, 10 хвилин
            call_data = call_tracker.get_call_by_target_and_time(target_number, time_range)
            if call_data:
                call_time_diff = current_time - call_data.get('timestamp', 0)
                logger.info(f"✅ Знайдено дзвінок по номеру {target_number} (різниця часу: {call_time_diff:.1f}с)")
                return call_data
    
    # 5. Останній шанс - пошук по всіх активних дзвінках
    logger.info("🔍 Останній шанс - пошук серед всіх активних дзвінків...")
    
    try:
        # Отримуємо всі активні дзвінки за останні 10 хвилин
        all_calls = call_tracker.get_recent_calls(600)
        
        for call in all_calls:
            call_target = normalize_phone_number(call.get('target_number', ''))
            
            # Перевіряємо чи це наш номер
            if call_target in ['637442017', '930063585']:
                call_time_diff = current_time - call.get('timestamp', 0)
                
                # Якщо дзвінок був нещодавно
                if call_time_diff < time_window:
                    logger.info(f"✅ Знайдено по часу: {call['call_id']} (різниця: {call_time_diff:.1f}с)")
                    return call
                    
    except Exception as e:
        logger.error(f"❌ Помилка пошуку серед активних дзвінків: {e}")
    
    logger.warning(f"❌ Дзвінок не знайдено жодним способом")
    return None

def main():
    """Головна функція обробки webhook"""
    try:
        # Отримуємо JSON данні з аргументів командного рядка
        if len(sys.argv) < 2:
            logger.error("❌ Не передано JSON данні")
            print(json.dumps({"success": False, "message": "No JSON data provided"}))
            sys.exit(1)
        
        json_data = sys.argv[1]
        logger.info(f"📥 Отримано данні: {json_data}")
        
        # Парсимо JSON
        try:
            webhook_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Помилка парсингу JSON: {e}")
            print(json.dumps({"success": False, "message": f"JSON parse error: {e}"}))
            sys.exit(1)
        
        event = webhook_data.get('event', '')
        pbx_call_id = webhook_data.get('pbx_call_id', '')
        caller_id = webhook_data.get('caller_id', '').replace('+', '')
        destination = webhook_data.get('destination', '')
        called_did = webhook_data.get('called_did', '')
        disposition = webhook_data.get('disposition', '')
        duration = int(webhook_data.get('duration', 0))
        
        logger.info(f"🔔 Webhook подія: {event}")
        logger.info(f"   PBX ID: {pbx_call_id}")
        logger.info(f"   Caller: {caller_id}")
        logger.info(f"   Destination: {destination}")
        logger.info(f"   Called DID: {called_did}")
        logger.info(f"   Disposition: {disposition}")
        logger.info(f"   Duration: {duration}")
        
        # Імпортуємо наш модуль webhook обробки
        try:
            from zadarma_api_webhook import process_webhook_call_status, send_telegram_message, call_tracker
            logger.info("✅ Успішно імпортовано zadarma_api_webhook")
        except ImportError as e:
            logger.error(f"❌ Помилка імпорту zadarma_api_webhook: {e}")
            try:
                from zadarma_api import process_webhook_call_status, send_telegram_message, call_tracker
                logger.info("✅ Fallback: імпортовано zadarma_api")
            except ImportError:
                logger.error("❌ Не вдалося імпортувати жодний модуль webhook обробки")
                print(json.dumps({"success": False, "message": "Import error"}))
                sys.exit(1)
        
        # Обробляємо різні типи подій
        if event == 'NOTIFY_END':
            logger.info(f"📞 Обробка завершення дзвінка")
            
            # ПОКРАЩЕНИЙ ПОШУК ДЗВІНКА
            call_data = find_tracked_call(pbx_call_id, caller_id, call_tracker)
            
            if call_data:
                logger.info(f"✅ Знайдено відстежуваний дзвінок: {call_data['call_id']}")
                
                action_name = "хвіртку" if call_data['action_type'] == 'hvirtka' else "ворота"
                chat_id = call_data['chat_id']
                
                # Детальний аналіз результату дзвінка
                message = ""
                status = ""
                
                if disposition == 'cancel' and duration == 0:
                    # ✅ УСПІХ: Дзвінок скинуто після гудків (система відповіла і скинула)
                    message = f"✅ {action_name.capitalize()} відчинено!"
                    status = 'success'
                    logger.info(f"✅ SUCCESS: {action_name} відкрито успішно")
                    
                elif disposition == 'busy':
                    # ❌ ЗАЙНЯТО  
                    message = f"❌ Номер {action_name} зайнятий. Спробуйте ще раз через хвилину."
                    status = 'busy'
                    logger.warning(f"❌ BUSY: {action_name} зайнято")
                    
                elif disposition in ['no-answer', 'noanswer'] and duration == 0:
                    # ❌ НЕ ВІДПОВІДАЄ
                    message = f"❌ Номер {action_name} не відповідає. Можливо проблеми зв'язку.\n\nСпробуйте ще раз або зателефонуйте нам за номером <a href=\"tel:+380733103110\">+380733103110</a>"
                    status = 'no_answer'
                    logger.warning(f"❌ NO_ANSWER: {action_name} не відповідає")
                    
                elif disposition == 'answered' and duration > 0:
                    # ⚠️ ПРОБЛЕМА: Дзвінок прийняли замість скидання
                    message = f"⚠️ Дзвінок для відкриття {action_name} було прийнято.\nМожливо, система не налаштована правильно.\n\nЗверніться до підтримки: <a href=\"tel:+380733103110\">+380733103110</a>"
                    status = 'answered'
                    logger.error(f"⚠️ ANSWERED: Проблема налаштування - дзвінок на {action_name} прийнято")
                    
                    # Сповіщаємо адміна про проблему
                    try:
                        from config import ADMIN_USER_ID
                        admin_message = f"🚨 ПРОБЛЕМА: Дзвінок на {action_name} ({call_data['target_number']}) було ПРИЙНЯТО замість скидання! Тривалість: {duration}s. Перевірте налаштування системи."
                        send_telegram_message(ADMIN_USER_ID, admin_message)
                    except Exception as admin_error:
                        logger.error(f"❌ Помилка відправки повідомлення адміну: {admin_error}")
                    
                else:
                    # ❌ ІНША ПОМИЛКА
                    message = f"❌ Не вдалося відкрити {action_name}.\nСтатус: {disposition}\nТривалість: {duration}s\n\nСпробуйте ще раз або зателефонуйте нам за номером <a href=\"tel:+380733103110\">+380733103110</a>"
                    status = 'failed'
                    logger.warning(f"❌ FAILED: {action_name} - {disposition}")
                
                # Відправляємо результат користувачу
                success = send_telegram_message(chat_id, message)
                
                if success:
                    logger.info(f"📤 Результат відправлено користувачу в чат {chat_id}: {status}")
                else:
                    logger.error(f"❌ Не вдалося відправити результат користувачу в чат {chat_id}")
                
                # Оновлюємо статус в базі
                call_tracker.update_call_status(call_data['call_id'], status, pbx_call_id)
                
                result = {
                    "success": True, 
                    "status": status, 
                    "message": f"Notification sent to chat {chat_id}",
                    "call_id": call_data['call_id'],
                    "action": action_name
                }
                
            else:
                logger.info(f"ℹ️ Дзвінок {pbx_call_id} ({caller_id}) не відстежується нашою системою")
                
                # Додаткова діагностика
                logger.info("🔍 ДОДАТКОВА ДІАГНОСТИКА:")
                logger.info(f"   Нормалізований caller_id: {normalize_phone_number(caller_id)}")
                
                # Показуємо активні дзвінки для діагностики
                try:
                    recent_calls = call_tracker.get_recent_calls(300)
                    logger.info(f"   Активних дзвінків за 5 хв: {len(recent_calls)}")
                    for call in recent_calls:
                        call_age = time.time() - call.get('timestamp', 0)
                        logger.info(f"     - {call['call_id']}: {call['target_number']} ({call_age:.1f}с тому)")
                except Exception as diag_error:
                    logger.error(f"   Помилка діагностики: {diag_error}")
                
                result = {"success": True, "message": "Call not tracked by our system"}
                
        elif event == 'NOTIFY_START':
            # Для початку дзвінка логуємо
            logger.info(f"📞 START: PBX ID {pbx_call_id}, Caller: {caller_id}")
            result = {"success": True, "message": "Start event logged"}
            
        elif event == 'NOTIFY_INTERNAL':
            # Логуємо внутрішні дзвінки
            internal = webhook_data.get('internal', '')
            logger.info(f"📞 INTERNAL: Caller {caller_id} -> Internal {internal}")
            result = {"success": True, "message": "Internal call logged"}
            
        else:
            logger.info(f"ℹ️ Подія {event} не потребує обробки")
            result = {"success": True, "message": f"Event {event} ignored"}
        
        # Виводимо результат для PHP
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
        
    except Exception as e:
        logger.exception(f"❌ Критична помилка в process_webhook: {e}")
        error_result = {"success": False, "message": str(e)}
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

echo -e "${GREEN}✅ Новий обробник встановлено${NC}"

# 3. Встановлюємо права
echo -e "${YELLOW}3️⃣ Встановлюємо права доступу...${NC}"
chmod +x process_webhook.py
echo -e "${GREEN}✅ Права встановлено${NC}"

# 4. Перевіряємо методи в zadarma_api_webhook.py
echo -e "${YELLOW}4️⃣ Перевіряємо методи CallTracker...${NC}"

# Додаємо методи якщо їх немає
python3 -c "
import sys
sys.path.append('/home/gomoncli/zadarma')
try:
    from zadarma_api_webhook import call_tracker
    if hasattr(call_tracker, 'get_recent_calls'):
        print('✅ Метод get_recent_calls існує')
    else:
        print('❌ Метод get_recent_calls відсутній')
    
    if hasattr(call_tracker, 'get_call_by_target_and_time'):
        print('✅ Метод get_call_by_target_and_time існує')
    else:
        print('❌ Метод get_call_by_target_and_time відсутній')
except Exception as e:
    print(f'❌ Помилка перевірки: {e}')
"

# 5. Тестуємо новий обробник
echo -e "${YELLOW}5️⃣ Тестуємо новий обробник...${NC}"

TEST_JSON='{"event":"NOTIFY_END","caller_id":"637442017","destination":"380733103110","pbx_call_id":"test_fix_123","disposition":"cancel","duration":"0"}'

echo "Тестові дані: $TEST_JSON"
echo "Результат тесту:"

python3 process_webhook.py "$TEST_JSON"

echo ""
echo -e "${GREEN}🎉 ВИПРАВЛЕННЯ РОЗГОРНУТО!${NC}"
echo ""
echo -e "${BLUE}📋 Що було зроблено:${NC}"
echo "1. ✅ Створено резервну копію старого файлу"
echo "2. ✅ Встановлено покращений обробник webhook"
echo "3. ✅ Додано розширений алгоритм пошуку дзвінків"
echo "4. ✅ Покращено логування та діагностику"
echo ""
echo -e "${YELLOW}🔍 Тепер зробіть тестовий дзвінок:${NC}"
echo "1. Викликайте /hvirtka в боті"
echo "2. Подивіться логи: tail -f webhook_processor.log"
echo "3. Перевірте чи приходить повідомлення про результат"
echo ""
echo -e "${BLUE}📊 Моніторинг логів:${NC}"
echo "tail -f /home/gomoncli/zadarma/webhook_processor.log"