#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_tracker_methods.py - Додає недостаючі методи в CallTracker
"""

import sys
import os

def add_methods_to_call_tracker():
    """Додає недостаючі методи до класу CallTracker"""
    
    file_path = '/home/gomoncli/zadarma/zadarma_api_webhook.py'
    
    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не знайдено")
        return False
    
    # Читаємо поточний файл
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Перевіряємо чи методи вже існують
    if 'def get_recent_calls(' in content and 'def get_call_by_target_and_time(' in content:
        print("✅ Методи вже існують")
        return True
    
    # Код методів для додавання
    methods_code = '''
    def get_recent_calls(self, time_window_seconds=300):
        """
        Отримує всі дзвінки за останній період
        
        Args:
            time_window_seconds: Вікно часу в секундах (за замовчуванням 5 хвилин)
        
        Returns:
            list: Список дзвінків
        """
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
            logger.error(f"❌ Помилка отримання нещодавніх дзвінків: {e}")
            return []

    def get_call_by_target_and_time(self, target_number, time_window_seconds=120):
        """
        Покращена функція пошуку дзвінка по номеру та часу
        
        Args:
            target_number: Цільовий номер телефону
            time_window_seconds: Вікно часу для пошуку
        
        Returns:
            dict або None: Дані дзвінка
        """
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - time_window_seconds
            
            cursor = self.conn.cursor()
            
            # Шукаємо по точній відповідності
            cursor.execute("""
                SELECT call_id, chat_id, target_number, action_type, timestamp, status, pbx_call_id
                FROM call_tracking 
                WHERE target_number = ? AND timestamp > ? AND status IN ('pending', 'api_success')
                ORDER BY timestamp DESC
                LIMIT 1
            """, (target_number, cutoff_time))
            
            row = cursor.fetchone()
            if row:
                return {
                    'call_id': row[0],
                    'chat_id': row[1],
                    'target_number': row[2], 
                    'action_type': row[3],
                    'timestamp': row[4],
                    'status': row[5],
                    'pbx_call_id': row[6]
                }
            
            # Якщо не знайдено точної відповідності, шукаємо по частковій
            # Нормалізуємо номер для пошуку
            normalized_target = target_number.lstrip('0').lstrip('38')
            
            cursor.execute("""
                SELECT call_id, chat_id, target_number, action_type, timestamp, status, pbx_call_id
                FROM call_tracking 
                WHERE (target_number LIKE ? OR target_number LIKE ?) 
                AND timestamp > ? AND status IN ('pending', 'api_success')
                ORDER BY timestamp DESC
                LIMIT 1
            """, (f'%{normalized_target}', f'%{target_number}%', cutoff_time))
            
            row = cursor.fetchone()
            if row:
                return {
                    'call_id': row[0],
                    'chat_id': row[1],
                    'target_number': row[2],
                    'action_type': row[3], 
                    'timestamp': row[4],
                    'status': row[5],
                    'pbx_call_id': row[6]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Помилка пошуку дзвінка по номеру {target_number}: {e}")
            return None
'''
    
    # Знаходимо місце для вставки (в кінці класу CallTracker)
    lines = content.split('\n')
    insert_index = -1
    
    # Шукаємо останній метод класу CallTracker
    in_call_tracker_class = False
    for i, line in enumerate(lines):
        if 'class CallTracker:' in line:
            in_call_tracker_class = True
        elif in_call_tracker_class and line.startswith('class ') and 'CallTracker' not in line:
            # Знайшли наступний клас
            insert_index = i
            break
        elif in_call_tracker_class and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            # Знайшли кінець класу
            insert_index = i
            break
    
    if insert_index == -1:
        # Додаємо в кінець файлу
        insert_index = len(lines)
    
    # Вставляємо методи
    method_lines = methods_code.split('\n')
    for i, method_line in enumerate(method_lines):
        lines.insert(insert_index + i, method_line)
    
    # Записуємо назад
    new_content = '\n'.join(lines)
    
    # Створюємо резервну копію
    backup_path = f"{file_path}.backup.tracker_methods"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Записуємо новий вміст
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Методи успішно додано до CallTracker")
    print(f"✅ Резервна копія: {backup_path}")
    return True

if __name__ == "__main__":
    print("🔧 Додавання недостаючих методів до CallTracker...")
    
    if add_methods_to_call_tracker():
        print("✅ Операція завершена успішно")
        
        # Тестуємо чи працює імпорт
        try:
            sys.path.append('/home/gomoncli/zadarma')
            from zadarma_api_webhook import call_tracker
            
            if hasattr(call_tracker, 'get_recent_calls'):
                print("✅ Метод get_recent_calls доступний")
            else:
                print("❌ Метод get_recent_calls недоступний")
                
            if hasattr(call_tracker, 'get_call_by_target_and_time'):
                print("✅ Метод get_call_by_target_and_time доступний")
            else:
                print("❌ Метод get_call_by_target_and_time недоступний")
                
        except Exception as e:
            print(f"⚠️ Помилка тестування: {e}")
            
    else:
        print("❌ Операція не вдалася")