#!/usr/bin/env python3
# Покращений webhook процесор з діагностикою
import sys
import json
import sqlite3
import time
import requests

def send_telegram(chat_id, message):
    try:
        # Читаємо токен з config
        with open('config.py', 'r') as f:
            config_content = f.read()
        
        import re
        token_match = re.search(r'TELEGRAM_TOKEN\s*=\s*[\'"]([^\'"]+)[\'"]', config_content)
        if not token_match:
            print("ERROR: Cannot find TELEGRAM_TOKEN")
            return False
            
        token = token_match.group(1)
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        
        response = requests.post(url, data=data, timeout=10)
        print(f"Telegram: {response.status_code} - {response.text}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def find_call_in_db(target_number, time_window=120):
    """Знаходить дзвінок в базі даних"""
    try:
        conn = sqlite3.connect('call_tracking.db')
        cursor = conn.cursor()
        
        current_time = int(time.time())
        time_start = current_time - time_window
        
        # Покращений пошук - спочатку точний номер
        cursor.execute('''
            SELECT call_id, user_id, chat_id, action_type, target_number, start_time, status
            FROM call_tracking 
            WHERE target_number = ? AND start_time > ? AND status = 'api_success'
            ORDER BY start_time DESC LIMIT 1
        ''', (target_number, time_start))
        
        result = cursor.fetchone()
        
        if not result:
            # Додатковий пошук для різних форматів номеру
            normalized = target_number.lstrip('0')
            cursor.execute('''
                SELECT call_id, user_id, chat_id, action_type, target_number, start_time, status
                FROM call_tracking 
                WHERE (target_number LIKE ? OR target_number LIKE ?) 
                AND start_time > ? AND status = 'api_success'
                ORDER BY start_time DESC LIMIT 1
            ''', (f'%{normalized}', f'%{target_number}%', time_start))
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
        print(f"DB error: {e}")
        return None

def main():
    print("=== ENHANCED WEBHOOK PROCESSOR ===")
    
    if len(sys.argv) < 2:
        print("ERROR: No webhook data provided")
        return
    
    try:
        data = json.loads(sys.argv[1])
        print(f"Received data: {data}")
        
        event = data.get('event', '')
        caller_id = data.get('caller_id', '')
        called_did = data.get('called_did', '') 
        disposition = data.get('disposition', '')
        duration = int(data.get('duration', 0))
        
        print(f"Event: {event}, From: {caller_id}, To: {called_did}")
        print(f"Disposition: {disposition}, Duration: {duration}")
        
        if event == 'NOTIFY_END':
            # Покращене визначення типу дзвінка
            target_number = None
            action_name = None
            
            print(f"DIAGNOSTIC: Checking called_did: '{called_did}'")
            
            if '637442017' in called_did:
                target_number = '0637442017'
                action_name = 'хвіртка'
                print("DETECTED: Хвіртка")
            elif '930063585' in called_did:
                target_number = '0930063585'
                action_name = 'ворота'
                print("DETECTED: Ворота")
            else:
                print(f"UNKNOWN TARGET: '{called_did}' - trying all possibilities")
                # Спробуємо всі можливі номери
                possible_numbers = ['0637442017', '0930063585']
                for num in possible_numbers:
                    if num[-7:] in called_did or num in called_did:
                        target_number = num
                        action_name = 'хвіртка' if '637442017' in num else 'ворота'
                        print(f"FOUND MATCH: {num} -> {action_name}")
                        break
                
                if not target_number:
                    print(f"NO MATCH FOUND for: {called_did}")
                    return
            
            print(f"Target: {target_number}, Action: {action_name}")
            
            # Шукаємо дзвінок в базі
            call_data = find_call_in_db(target_number)
            
            if call_data:
                print(f"Found call: {call_data['call_id']}")
                
                # ВИПРАВЛЕНА логіка успіху
                if disposition == 'cancel' and duration > 0:
                    message = f"✅ {action_name.capitalize()} відчинено!"
                    status = 'success'
                elif disposition == 'busy':
                    message = f"❌ Номер {action_name} зайнятий. Спробуйте ще раз."
                    status = 'busy'
                elif disposition in ['no-answer', 'noanswer', 'cancel'] and duration == 0:
                    message = f"❌ Номер {action_name} не відповідає."
                    status = 'no_answer'
                else:
                    message = f"❌ Не вдалося відкрити {action_name}. Статус: {disposition}"
                    status = 'failed'
                
                print(f"Result: {status} - {message}")
                
                # Відправляємо повідомлення
                chat_id = call_data['chat_id']
                success = send_telegram(chat_id, message)
                
                if success:
                    print("✅ Message sent successfully!")
                else:
                    print("❌ Failed to send message")
                
                # Оновлюємо статус в базі
                try:
                    conn = sqlite3.connect('call_tracking.db')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE call_tracking SET status = ? WHERE call_id = ?', 
                                 (status, call_data['call_id']))
                    conn.commit()
                    conn.close()
                    print("✅ Status updated in DB")
                except Exception as e:
                    print(f"DB update error: {e}")
                
            else:
                print(f"❌ Call not found for {target_number}")
                # DIAGNOSTIC: показати останні записи
                try:
                    conn = sqlite3.connect('call_tracking.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT call_id, action_type, target_number, status FROM call_tracking ORDER BY created_at DESC LIMIT 5')
                    recent = cursor.fetchall()
                    conn.close()
                    print("RECENT CALLS:")
                    for r in recent:
                        print(f"  {r[0]} - {r[1]} - {r[2]} - {r[3]}")
                except Exception as e:
                    print(f"DIAGNOSTIC ERROR: {e}")
        
        print("=== WEBHOOK PROCESSING COMPLETE ===")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
