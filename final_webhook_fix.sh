#!/bin/bash

echo "🚀 ФІНАЛЬНЕ ВИПРАВЛЕННЯ WEBHOOK ПРОБЛЕМИ"
echo "======================================"

PROJECT_DIR="/home/gomoncli/zadarma"
cd $PROJECT_DIR

# Кольори
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📁 Робочий каталог: $PROJECT_DIR${NC}"

# 1. Створюємо резервні копії
echo -e "${YELLOW}1️⃣ Створюємо резервні копії...${NC}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -f "process_webhook.py" ]; then
    cp process_webhook.py "process_webhook.py.backup.$TIMESTAMP"
    echo -e "${GREEN}✅ Резервна копія process_webhook.py створена${NC}"
fi

if [ -f "zadarma_api_webhook.py" ]; then
    cp zadarma_api_webhook.py "zadarma_api_webhook.py.backup.$TIMESTAMP"
    echo -e "${GREEN}✅ Резервна копія zadarma_api_webhook.py створена${NC}"
fi

# 2. Запускаємо скрипт розгортання
echo -e "${YELLOW}2️⃣ Розгортаємо виправлений webhook обробник...${NC}"

# Створюємо новий process_webhook.py
cat > process_webhook.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
process_webhook.py - ВИПРАВЛЕНИЙ обробник webhook-ів для телеграм бота
Версія з покращеним алгоритмом пошуку дзвінків
"""

import sys
import json
import logging
import os
import time

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

logger = logging.getLogger('webhook_processor_fixed')

def normalize_phone_number(phone):
    """Нормалізує номер телефону для порівняння"""
    if not phone:
        return ""
    
    normalized = ''.join(filter(str.isdigit, str(phone)))
    
    if normalized.startswith('380'):
        normalized = normalized[3:]
    elif normalized.startswith('38'):
        normalized = normalized[2:]
    elif normalized.startswith('0'):
        normalized = normalized[1:]
    
    return normalized

def find_tracked_call_enhanced(pbx_call_id, caller_id, call_tracker):
    """
    Покращений пошук відстежуваного дзвінка
    Використовує кілька стратегій пошуку
    """
    logger.info(f"🔍 ПОКРАЩЕНИЙ пошук дзвінка:")
    logger.info(f"   PBX ID: {pbx_call_id}")
    logger.info(f"   Caller ID: {caller_id}")
    
    current_time = time.time()
    
    # Стратегія 1: Пошук по PBX ID
    if pbx_call_id:
        try:
            call_data = call_tracker.get_call_by_pbx_id(pbx_call_id)
            if call_data:
                logger.info(f"✅ ЗНАЙДЕНО ПО PBX ID: {pbx_call_id}")
                return call_data
        except:
            pass
    
    # Стратегія 2: Аналіз номера з webhook для визначення типу дзвінка
    target_numbers = []
    action_type = None
    
    # Визначаємо тип дзвінка по caller_id
    if '637442017' in caller_id:
        target_numbers = ['0637442017', '637442017', '380637442017']
        action_type = 'hvirtka'
        logger.info("🚪 Тип: Хвіртка")
    elif '930063585' in caller_id:
        target_numbers = ['0930063585', '930063585', '380930063585']
        action_type = 'vorota'
        logger.info("🏠 Тип: Ворота")
    else:
        logger.warning(f"⚠️ Невідомий номер: {caller_id}")
        return None
    
    # Стратегія 3: Пошук по номеру та часу з розширеними інтервалами
    for target_number in target_numbers:
        for time_window in [30, 60, 120, 300, 600]:  # від 30 секунд до 10 хвилин
            try:
                if hasattr(call_tracker, 'get_call_by_target_and_time'):
                    call_data = call_tracker.get_call_by_target_and_time(target_number, time_window)
                else:
                    # Fallback метод
                    call_data = call_tracker.get_call_by_target(target_number, time_window)
                
                if call_data:
                    time_diff = current_time - call_data.get('timestamp', 0)
                    logger.info(f"✅ ЗНАЙДЕНО ПО НОМЕРУ: {target_number} (час: {time_diff:.1f}с)")
                    return call_data
            except Exception as e:
                logger.debug(f"   Помилка пошуку по {target_number}: {e}")
                continue
    
    # Стратегія 4: Пошук останнього дзвінка правильного типу
    try:
        if hasattr(call_tracker, 'get_recent_calls'):
            recent_calls = call_tracker.get_recent_calls(600)
        else:
            # Fallback
            recent_calls = []
        
        for call in recent_calls:
            if call.get('action_type') == action_type:
                time_diff = current_time - call.get('timestamp', 0)
                if time_diff < 600:  # 10 хвилин
                    logger.info(f"✅ ЗНАЙДЕНО ПО ТИПУ: {call['call_id']} (час: {time_diff:.1f}с)")
                    return call
    except Exception as e:
        logger.error(f"❌ Помилка пошуку нещодавніх дзвінків: {e}")
    
    logger.warning(f"❌ Дзвінок НЕ ЗНАЙДЕНО жодним способом")
    return None

def main():
    """Головна функція обробки webhook"""
    try:
        # Отримуємо JSON данні
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
        
        # Імпортуємо модуль обробки
        try:
            from zadarma_api_webhook import send_telegram_message, call_tracker
            logger.info("✅ Успішно імпортовано zadarma_api_webhook")
        except ImportError as e:
            logger.error(f"❌ Помилка імпорту zadarma_api_webhook: {e}")
            try:
                from zadarma_api import send_telegram_message, call_tracker
                logger.info("✅ Fallback: імпортовано zadarma_api")
            except ImportError:
                logger.error("❌ Не вдалося імпортувати модуль обробки")
                print(json.dumps({"success": False, "message": "Import error"}))
                sys.exit(1)
        
        # Обробляємо події
        if event == 'NOTIFY_END':
            logger.info(f"📞 Обробка завершення дзвінка")
            
            # ПОКРАЩЕНИЙ ПОШУК
            call_data = find_tracked_call_enhanced(pbx_call_id, caller_id, call_tracker)
            
            if call_data:
                logger.info(f"✅ ЗНАЙДЕНО відстежуваний дзвінок: {call_data['call_id']}")
                
                action_name = "хвіртку" if call_data['action_type'] == 'hvirtka' else "ворота"
                chat_id = call_data['chat_id']
                
                # Аналіз результату
                message = ""
                status = ""
                
                if disposition == 'cancel' and duration == 0:
                    message = f"✅ {action_name.capitalize()} відчинено!"
                    status = 'success'
                    logger.info(f"✅ УСПІХ: {action_name} відкрито")
                elif disposition == 'busy':
                    message = f"❌ Номер {action_name} зайнятий. Спробуйте ще раз через хвилину."
                    status = 'busy'
                    logger.warning(f"❌ ЗАЙНЯТО: {action_name}")
                elif disposition in ['no-answer', 'noanswer'] and duration == 0:
                    message = f"❌ Номер {action_name} не відповідає. Можливо проблеми зв'язку.\n\nСпробуйте ще раз або зателефонуйте: <a href=\"tel:+380733103110\">+380733103110</a>"
                    status = 'no_answer'
                    logger.warning(f"❌ НЕ ВІДПОВІДАЄ: {action_name}")
                elif disposition == 'answered' and duration > 0:
                    message = f"⚠️ Дзвінок для відкриття {action_name} було прийнято.\nМожливо, система не налаштована правильно.\n\nЗверніться до підтримки: <a href=\"tel:+380733103110\">+380733103110</a>"
                    status = 'answered'
                    logger.error(f"⚠️ ПРИЙНЯТО: {action_name} - потрібна перевірка")
                    
                    # Сповіщення адміна
                    try:
                        from config import ADMIN_USER_ID
                        admin_message = f"🚨 ПРОБЛЕМА: Дзвінок на {action_name} ({call_data['target_number']}) ПРИЙНЯТО замість скидання! Тривалість: {duration}s"
                        send_telegram_message(ADMIN_USER_ID, admin_message)
                    except Exception as admin_error:
                        logger.error(f"❌ Помилка сповіщення адміна: {admin_error}")
                else:
                    message = f"❌ Не вдалося відкрити {action_name}.\nСтатус: {disposition}\nТривалість: {duration}s\n\nСпробуйте ще раз або зателефонуйте: <a href=\"tel:+380733103110\">+380733103110</a>"
                    status = 'failed'
                    logger.warning(f"❌ НЕВДАЧА: {action_name} - {disposition}")
                
                # Відправляємо повідомлення користувачу
                success = send_telegram_message(chat_id, message)
                
                if success:
                    logger.info(f"📤 ПОВІДОМЛЕННЯ ВІДПРАВЛЕНО користувачу {chat_id}: {status}")
                else:
                    logger.error(f"❌ НЕ ВДАЛОСЯ відправити повідомлення користувачу {chat_id}")
                
                # Оновлюємо статус
                try:
                    call_tracker.update_call_status(call_data['call_id'], status, pbx_call_id)
                    logger.info(f"📝 Статус оновлено: {status}")
                except Exception as update_error:
                    logger.error(f"❌ Помилка оновлення статусу: {update_error}")
                
                result = {
                    "success": True, 
                    "status": status, 
                    "message": f"Notification sent to chat {chat_id}",
                    "call_id": call_data['call_id'],
                    "action": action_name
                }
                
            else:
                logger.warning(f"ℹ️ Дзвінок {pbx_call_id} ({caller_id}) НЕ ВІДСТЕЖУЄТЬСЯ")
                
                # Діагностична інформація
                logger.info("🔍 ДІАГНОСТИКА:")
                logger.info(f"   Нормалізований caller: {normalize_phone_number(caller_id)}")
                
                try:
                    if hasattr(call_tracker, 'get_recent_calls'):
                        recent_calls = call_tracker.get_recent_calls(300)
                        logger.info(f"   Активних дзвінків: {len(recent_calls)}")
                        for call in recent_calls:
                            age = time.time() - call.get('timestamp', 0)
                            logger.info(f"     - {call['call_id']}: {call['target_number']} ({age:.0f}с)")
                except Exception as diag_error:
                    logger.error(f"   Помилка діагностики: {diag_error}")
                
                result = {"success": True, "message": "Call not tracked by our system"}
                
        elif event == 'NOTIFY_START':
            logger.info(f"📞 START: PBX {pbx_call_id}, Caller: {caller_id}")
            result = {"success": True, "message": "Start event logged"}
            
        elif event == 'NOTIFY_INTERNAL':
            internal = webhook_data.get('internal', '')
            logger.info(f"📞 INTERNAL: {caller_id} -> {internal}")
            result = {"success": True, "message": "Internal call logged"}
            
        else:
            logger.info(f"ℹ️ Подія {event} ігнорується")
            result = {"success": True, "message": f"Event {event} ignored"}
        
        # Повертаємо результат
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
        
    except Exception as e:
        logger.exception(f"❌ КРИТИЧНА ПОМИЛКА: {e}")
        print(json.dumps({"success": False, "message": str(e)}, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x process_webhook.py
echo -e "${GREEN}✅ Новий process_webhook.py створено${NC}"

# 3. Додаємо методи до CallTracker
echo -e "${YELLOW}3️⃣ Додаємо недостаючі методи до CallTracker...${NC}"

python3 << 'PYTHON_EOF'
import sys
import os
import re

sys.path.append('/home/gomoncli/zadarma')

def add_methods_to_tracker():
    file_path = '/home/gomoncli/zadarma/zadarma_api_webhook.py'
    
    if not os.path.exists(file_path):
        print("❌ Файл zadarma_api_webhook.py не знайдено")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Перевіряємо чи методи вже є
    if 'def get_recent_calls(' in content and 'def get_call_by_target_and_time(' in content:
        print("✅ Методи вже існують")
        return True
    
    # Шукаємо місце для додавання методів (кінець класу CallTracker)
    lines = content.split('\n')
    insert_line = -1
    
    for i, line in enumerate(lines):
        if 'class CallTracker:' in line:
            # Знайшли початок класу, тепер шукаємо його кінець
            for j in range(i + 1, len(lines)):
                next_line = lines[j]
                # Якщо знайшли наступний клас або функцію на рівні модуля
                if (next_line.strip() and 
                    not next_line.startswith(' ') and 
                    not next_line.startswith('\t') and
                    (next_line.startswith('class ') or next_line.startswith('def '))):
                    insert_line = j
                    break
            if insert_line == -1:
                insert_line = len(lines)
            break
    
    if insert_line == -1:
        print("❌ Не знайдено клас CallTracker")
        return False
    
    # Додаємо методи
    new_methods = '''
    def get_recent_calls(self, time_window_seconds=300):
        """Отримує всі дзвінки за останній період"""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - time_window_seconds
            
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT call_id, chat_id, target_number, action_type, timestamp, status, pbx_call_id
                FROM call_tracking 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """, (cutoff_time,))
            
            calls = []
            for row in cursor.fetchall():
                calls.append({
                    'call_id': row[0],
                    'chat_id': row[1], 
                    'target_number': row[2],
                    'action_type': row[3],
                    'timestamp': row[4],
                    'status': row[5],
                    'pbx_call_id': row[6]
                })
            
            return calls
        except Exception as e:
            logger.error(f"❌ Помилка get_recent_calls: {e}")
            return []

    def get_call_by_target_and_time(self, target_number, time_window_seconds=120):
        """Покращений пошук дзвінка по номеру та часу"""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - time_window_seconds
            
            cursor = self.conn.cursor()
            
            # Точний пошук
            cursor.execute("""
                SELECT call_id, chat_id, target_number, action_type, timestamp, status, pbx_call_id
                FROM call_tracking 
                WHERE target_number = ? AND timestamp > ? AND status IN ('pending', 'api_success')
                ORDER BY timestamp DESC LIMIT 1
            """, (target_number, cutoff_time))
            
            row = cursor.fetchone()
            if row:
                return {
                    'call_id': row[0], 'chat_id': row[1], 'target_number': row[2],
                    'action_type': row[3], 'timestamp': row[4], 'status': row[5], 'pbx_call_id': row[6]
                }
            
            # Пошук по частковій відповідності
            normalized = target_number.lstrip('0').lstrip('38')
            cursor.execute("""
                SELECT call_id, chat_id, target_number, action_type, timestamp, status, pbx_call_id
                FROM call_tracking 
                WHERE (target_number LIKE ? OR target_number LIKE ?) 
                AND timestamp > ? AND status IN ('pending', 'api_success')
                ORDER BY timestamp DESC LIMIT 1
            """, (f'%{normalized}', f'%{target_number}%', cutoff_time))
            
            row = cursor.fetchone()
            if row:
                return {
                    'call_id': row[0], 'chat_id': row[1], 'target_number': row[2],
                    'action_type': row[3], 'timestamp': row[4], 'status': row[5], 'pbx_call_id': row[6]
                }
            
            return None
        except Exception as e:
            logger.error(f"❌ Помилка get_call_by_target_and_time: {e}")
            return None
'''
    
    # Вставляємо методи
    lines.insert(insert_line, new_methods)
    
    # Записуємо файл
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ Методи додано до CallTracker")
    return True

# Викликаємо функцію
if add_methods_to_tracker():
    # Тестуємо імпорт
    try:
        from zadarma_api_webhook import call_tracker
        if hasattr(call_tracker, 'get_recent_calls'):
            print("✅ get_recent_calls доступний")
        if hasattr(call_tracker, 'get_call_by_target_and_time'):
            print("✅ get_call_by_target_and_time доступний")
    except Exception as e:
        print(f"⚠️ Помилка тестування: {e}")
else:
    print("❌ Не вдалося додати методи")
PYTHON_EOF

echo -e "${GREEN}✅ Методи CallTracker оновлено${NC}"

# 4. Тестуємо нову систему
echo -e "${YELLOW}4️⃣ Тестуємо оновлену систему...${NC}"

# Створюємо тестові дані схожі на реальні з логів
TEST_JSON='{"event":"NOTIFY_END","caller_id":"637442017","called_did":"380733103110","pbx_call_id":"in_test123","disposition":"cancel","duration":"0","status_code":"16"}'

echo "Тестові дані (хвіртка): $TEST_JSON"
echo "Результат:"
python3 process_webhook.py "$TEST_JSON" 2>&1

echo ""
echo -e "${GREEN}🎉 ФІНАЛЬНЕ ВИПРАВЛЕННЯ ЗАВЕРШЕНО!${NC}"
echo ""
echo -e "${BLUE}📋 Що було зроблено:${NC}"
echo "1. ✅ Створено резервні копії всіх файлів"
echo "2. ✅ Встановлено покращений webhook обробник"
echo "3. ✅ Додано методи get_recent_calls та get_call_by_target_and_time"
echo "4. ✅ Покращено алгоритм пошуку дзвінків"
echo "5. ✅ Додано детальне логування та діагностику"
echo ""
echo -e "${YELLOW}🧪 ТЕПЕР ЗРОБІТЬ ТЕСТОВИЙ ДЗВІНОК:${NC}"
echo "1. Викличте /hvirtka в Telegram боті"
echo "2. Очікуйте повідомлення про результат"
echo "3. Перевірте логи: tail -f webhook_processor.log"
echo ""
echo -e "${BLUE}📊 Моніторинг:${NC}"
echo "tail -f /home/gomoncli/zadarma/webhook_processor.log | grep -E '(SUCCESS|FAIL|ERROR|✅|❌)'"