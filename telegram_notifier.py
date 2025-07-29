#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
telegram_notifier.py - Telegram сповіщення для API моніторингу
"""

import requests
import json
import logging
import os
from datetime import datetime
from config import TELEGRAM_TOKEN, ADMIN_USER_ID

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.token = TELEGRAM_TOKEN
        self.admin_id = ADMIN_USER_ID
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.state_file = "/home/gomoncli/zadarma/api_states.json"
    
    def send_message(self, message, parse_mode="HTML"):
        """Відправити повідомлення адміністратору"""
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.admin_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Помилка відправки Telegram: {e}")
            return False
    
    def load_previous_states(self):
        """Завантажити попередні стани API"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_states(self, states):
        """Зберегти поточні стани API"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(states, f)
        except Exception as e:
            logger.error(f"Помилка збереження станів: {e}")
    
    def notify_critical_error(self, api_name, error_message):
        """Критична помилка API"""
        message = f"""
🚨 <b>КРИТИЧНА ПОМИЛКА API</b>

📡 <b>API:</b> {api_name.upper()}
❌ <b>Помилка:</b> {error_message}
🕐 <b>Час:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚡ <b>Потрібна негайна увага!</b>
        """
        return self.send_message(message.strip())
    
    def notify_api_recovery(self, api_name):
        """API відновлено"""
        message = f"""
✅ <b>API ВІДНОВЛЕНО</b>

📡 <b>API:</b> {api_name.upper()}
🕐 <b>Час:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

😊 Все працює нормально!
        """
        return self.send_message(message.strip())
    
    def notify_regular_error(self, api_name, error_message):
        """Звичайна помилка API"""
        message = f"""
⚠️ <b>Помилка API</b>

📡 <b>API:</b> {api_name.upper()}
❌ <b>Помилка:</b> {error_message}
🕐 <b>Час:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return self.send_message(message.strip())
    
    def send_daily_summary(self, results):
        """Щоденний звіт"""
        ok_count = sum(1 for r in results.values() if r['status'] == 'OK')
        total = len(results)
        
        status_emoji = "✅" if ok_count == total else "⚠️" if ok_count >= total//2 else "❌"
        
        message = f"""
📊 <b>ЩОДЕННИЙ ЗВІТ API</b>

{status_emoji} <b>Статус:</b> {ok_count}/{total} API працюють

<b>Детально:</b>
"""
        
        for api_name, result in results.items():
            emoji = "✅" if result['status'] == 'OK' else "❌"
            message += f"{emoji} <b>{api_name.upper()}:</b> {result['message']}\n"
        
        message += f"\n🕐 <b>Час звіту:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_message(message.strip())
    
    def process_api_results(self, current_results):
        """Обробити результати API та відправити сповіщення"""
        previous_states = self.load_previous_states()
        notifications_sent = []
        
        critical_apis = ['zadarma', 'telegram']
        
        for api_name, result in current_results.items():
            current_status = result['status']
            previous_status = previous_states.get(api_name, 'UNKNOWN')
            
            # Сповіщення про нові помилки
            if current_status == 'ERROR' and previous_status != 'ERROR':
                if api_name in critical_apis:
                    self.notify_critical_error(api_name, result['message'])
                    notifications_sent.append(f"CRITICAL: {api_name}")
                else:
                    self.notify_regular_error(api_name, result['message'])
                    notifications_sent.append(f"ERROR: {api_name}")
            
            # Сповіщення про відновлення
            elif current_status == 'OK' and previous_status == 'ERROR':
                self.notify_api_recovery(api_name)
                notifications_sent.append(f"RECOVERY: {api_name}")
        
        # Зберегти поточні стани
        current_states = {api: result['status'] for api, result in current_results.items()}
        self.save_states(current_states)
        
        return notifications_sent

def test_notifier():
    """Тест сповіщувача"""
    notifier = TelegramNotifier()
    return notifier.send_message("🧪 <b>ТЕСТ СИСТЕМИ СПОВІЩЕНЬ</b>\n\n✅ Telegram сповіщення для API моніторингу працюють!")

if __name__ == "__main__":
    print("🧪 Тестування Telegram сповіщень...")
    success = test_notifier()
    print("✅ Успішно відправлено!" if success else "❌ Помилка відправки!")
