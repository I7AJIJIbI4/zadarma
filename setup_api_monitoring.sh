#!/bin/bash
# ДОДАВАННЯ ПЕРЕВІРКИ API ДО СИСТЕМИ ОБСЛУГОВУВАННЯ

cd /home/gomoncli/zadarma

echo "🚀 ЗАПОЧАТКОВУВАННЯ СИСТЕМИ МОНІТОРИНГУ API..."
echo "=============================================="

# 1. Створити модуль перевірки API
echo "📦 Створення api_monitor.py..."
cat > api_monitor.py << 'EOD'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api_monitor.py - Моніторинг доступності всіх API сервісів
"""

import requests
import json
import logging
import time
from config import (
    ZADARMA_API_KEY, ZADARMA_API_SECRET,
    WLAUNCH_API_KEY, COMPANY_ID
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIMonitor:
    def __init__(self):
        self.results = {}
    
    def test_zadarma_api(self):
        """Тестування Zadarma API"""
        try:
            from zadarma_api import test_zadarma_auth
            if test_zadarma_auth():
                self.results['zadarma'] = {'status': 'OK', 'message': 'API працює'}
                return True
            else:
                self.results['zadarma'] = {'status': 'ERROR', 'message': 'Помилка авторизації'}
                return False
        except Exception as e:
            self.results['zadarma'] = {'status': 'ERROR', 'message': str(e)}
            return False
    
    def test_wlaunch_api(self):
        """Тестування WLaunch API"""
        try:
            url = "https://wlaunch.wlapi.net/api/v1/companies"
            headers = {
                'Authorization': f'Bearer {WLAUNCH_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    self.results['wlaunch'] = {'status': 'OK', 'message': f'API працює, компаній: {len(data["data"])}'}
                    return True
            
            self.results['wlaunch'] = {'status': 'ERROR', 'message': f'HTTP {response.status_code}'}
            return False
            
        except Exception as e:
            self.results['wlaunch'] = {'status': 'ERROR', 'message': str(e)}
            return False
    
    def test_sms_fly_api(self):
        """Тестування SMS Fly API"""
        try:
            # Перевіряємо чи є SMS Fly конфігурація
            try:
                from config import SMS_FLY_LOGIN, SMS_FLY_PASSWORD
            except ImportError:
                self.results['sms_fly'] = {'status': 'NOT_CONFIGURED', 'message': 'SMS Fly не налаштовано'}
                return None
            
            url = "http://sms-fly.ua/api/api.php"
            params = {
                'login': SMS_FLY_LOGIN,
                'password': SMS_FLY_PASSWORD,
                'action': 'getbalance'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.text.strip()
                if result.replace('.', '').isdigit():
                    balance = float(result)
                    self.results['sms_fly'] = {'status': 'OK', 'message': f'Баланс: {balance} грн'}
                    return True
                else:
                    self.results['sms_fly'] = {'status': 'ERROR', 'message': f'Відповідь: {result}'}
                    return False
            
            self.results['sms_fly'] = {'status': 'ERROR', 'message': f'HTTP {response.status_code}'}
            return False
            
        except Exception as e:
            self.results['sms_fly'] = {'status': 'ERROR', 'message': str(e)}
            return False
    
    def test_telegram_api(self):
        """Тестування Telegram Bot API"""
        try:
            from config import TELEGRAM_TOKEN
            
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data['result']
                    self.results['telegram'] = {'status': 'OK', 'message': f'Бот: {bot_info["first_name"]}'}
                    return True
            
            self.results['telegram'] = {'status': 'ERROR', 'message': f'HTTP {response.status_code}'}
            return False
            
        except Exception as e:
            self.results['telegram'] = {'status': 'ERROR', 'message': str(e)}
            return False
    
    def run_all_tests(self):
        """Запуск всіх тестів API"""
        logger.info("🔍 Початок тестування всіх API...")
        
        tests = [
            ('Zadarma API', self.test_zadarma_api),
            ('WLaunch API', self.test_wlaunch_api),
            ('SMS Fly API', self.test_sms_fly_api),
            ('Telegram API', self.test_telegram_api)
        ]
        
        for name, test_func in tests:
            logger.info(f"🧪 Тестування {name}...")
            try:
                test_func()
            except Exception as e:
                logger.error(f"❌ Помилка тестування {name}: {e}")
                self.results[name.lower().replace(' ', '_')] = {'status': 'ERROR', 'message': str(e)}
        
        return self.results
    
    def get_summary(self):
        """Отримати підсумок тестування"""
        if not self.results:
            return "❓ Тестування не проводилось"
        
        ok_count = sum(1 for r in self.results.values() if r['status'] == 'OK')
        error_count = sum(1 for r in self.results.values() if r['status'] == 'ERROR')
        not_configured = sum(1 for r in self.results.values() if r['status'] == 'NOT_CONFIGURED')
        
        total = len(self.results)
        
        if error_count == 0:
            return f"✅ Всі API працюють ({ok_count}/{total})"
        elif error_count <= 1:
            return f"⚠️ Незначні проблеми з API ({ok_count}/{total} працюють)"
        else:
            return f"❌ Серйозні проблеми з API ({error_count}/{total} не працюють)"
    
    def get_detailed_report(self):
        """Детальний звіт по кожному API"""
        if not self.results:
            return "Немає результатів тестування"
        
        report = []
        for api_name, result in self.results.items():
            status_emoji = {
                'OK': '✅',
                'ERROR': '❌', 
                'NOT_CONFIGURED': '⚙️'
            }.get(result['status'], '❓')
            
            report.append(f"{status_emoji} {api_name.upper()}: {result['message']}")
        
        return "\n".join(report)

def main():
    """Головна функція для CLI використання"""
    monitor = APIMonitor()
    results = monitor.run_all_tests()
    
    print("\n📊 РЕЗУЛЬТАТИ ТЕСТУВАННЯ API:")
    print("=" * 40)
    print(monitor.get_detailed_report())
    print("=" * 40)
    print(monitor.get_summary())
    
    # Повертаємо код виходу
    error_count = sum(1 for r in results.values() if r['status'] == 'ERROR')
    return min(error_count, 10)  # Максимум 10 для exit code

if __name__ == "__main__":
    exit(main())
EOD

chmod +x api_monitor.py
echo "✅ api_monitor.py створено"

# 2. Пропустити зміни config.py - користувач налаштує вручну
echo "ℹ️ Пропускаємо автоматичне редагування config.py (зроблено за запитом)"

# 3. Оновити daily_maintenance.sh для включення API перевірок
echo "🔧 Додавання API перевірок до daily_maintenance.sh..."

# Створити backup
cp daily_maintenance.sh daily_maintenance.sh.backup.$(date +%Y%m%d_%H%M%S)

# Додати API секцію до daily_maintenance.sh
cat >> daily_maintenance.sh << 'EOD'

# ============================================
# ЧАСТИНА 6: МОНІТОРИНГ API СЕРВІСІВ
# ============================================

log_message "🌐 МОНІТОРИНГ API СЕРВІСІВ"
log_message "========================="

cd "$ZADARMA_DIR"

# 6.1 Запуск тестування API
log_message "1️⃣ Тестування всіх API сервісів..."
if python3 api_monitor.py > /tmp/api_test_output.txt 2>&1; then
    API_EXIT_CODE=$?
    log_message "✅ API тестування завершено (код: $API_EXIT_CODE)"
    
    # Логуємо результати
    while IFS= read -r line; do
        log_message "   $line"
    done < /tmp/api_test_output.txt
    
    # Якщо є помилки API - додаємо до лічільника помилок
    if [ "$API_EXIT_CODE" -gt 0 ]; then
        ERROR_COUNT=$((ERROR_COUNT + API_EXIT_CODE))
        log_message "⚠️ Виявлено $API_EXIT_CODE проблем з API"
    fi
else
    log_message "❌ Помилка запуску API тестування"
    ERROR_COUNT=$((ERROR_COUNT + 5))
fi

# 6.2 Перевірка специфічних API параметрів
log_message "2️⃣ Додаткові перевірки API..."

# Zadarma баланс (якщо API працює)
if python3 -c "from zadarma_api import test_zadarma_auth; exit(0 if test_zadarma_auth() else 1)" 2>/dev/null; then
    log_message "✅ Zadarma API доступний"
else
    log_message "❌ Zadarma API недоступний"
fi

# WLaunch підключення
WLAUNCH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://wlaunch.wlapi.net/api/v1/companies" \
    -H "Authorization: Bearer $(python3 -c "from config import WLAUNCH_API_KEY; print(WLAUNCH_API_KEY)" 2>/dev/null)" 2>/dev/null || echo "000")

if [ "$WLAUNCH_STATUS" = "200" ]; then
    log_message "✅ WLaunch API доступний (HTTP: $WLAUNCH_STATUS)"
else
    log_message "❌ WLaunch API недоступний (HTTP: $WLAUNCH_STATUS)"
fi

rm -f /tmp/api_test_output.txt
EOD

echo "✅ daily_maintenance.sh оновлено"

# 4. Створити окремий скрипт для перевірки тільки API
echo "📝 Створення api_check.sh..."

cat > api_check.sh << 'EOD'
#!/bin/bash
# ШВИДКА ПЕРЕВІРКА ВСІХ API

echo "🌐 ПЕРЕВІРКА API СЕРВІСІВ $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================="

cd /home/gomoncli/zadarma

if [ -f "api_monitor.py" ]; then
    python3 api_monitor.py
else
    echo "❌ api_monitor.py не знайдено"
    exit 1
fi
EOD

chmod +x api_check.sh
echo "✅ api_check.sh створено"

# 5. Додати API перевірку до cron (кожні 2 години)
echo "⏰ Налаштування автоматичних перевірок..."

# Перевірити чи вже є запис в crontab
CRON_EXISTS=$(crontab -l 2>/dev/null | grep -c "api_check.sh" || echo "0")

if [ "$CRON_EXISTS" -eq 0 ]; then
    # Додати до crontab
    (crontab -l 2>/dev/null; echo "0 */2 * * * /home/gomoncli/zadarma/api_check.sh >> /home/gomoncli/api_monitor.log 2>&1") | crontab -
    echo "✅ Cron налаштовано: перевірка кожні 2 години"
else
    echo "ℹ️ Cron вже налаштовано для API перевірок"
fi

# 6. Створити початковий звіт
echo "📊 Створення початкового звіту..."
python3 api_monitor.py > initial_api_report.txt 2>&1
echo "✅ Звіт збережено в initial_api_report.txt"

echo ""
echo "🎉 СИСТЕМА МОНІТОРИНГУ API СТВОРЕНА!"
echo "====================================="
echo ""
echo "📋 НОВІ КОМАНДИ:"
echo "   ./api_monitor.py           - Повна перевірка всіх API"
echo "   ./api_check.sh            - Швидка перевірка API"
echo ""
echo "⏰ АВТОМАТИЧНІ ПЕРЕВІРКИ:"
echo "   Кожні 2 години           - Перевірка всіх API"
echo "   Щодня о 06:00            - API перевірка в складі повного обслуговування"
echo ""
echo "📊 ПЕРЕВІРИТИ ЗАРАЗ:"
echo "   python3 api_monitor.py"
echo ""
echo "⚙️ ДЛЯ ПОВНОГО ФУНКЦІОНУВАННЯ ДОДАЙТЕ В config.py:"
echo "   # SMS Fly API"
echo "   SMS_FLY_LOGIN = \"ваш_логін\""
echo "   SMS_FLY_PASSWORD = \"ваш_пароль\""
echo "   SMS_FLY_SENDER = \"INFO\""
echo ""
echo "   # Telegram Bot API (опціонально)"
echo "   TELEGRAM_TOKEN = \"ваш_токен_бота\""
echo "   TELEGRAM_CHAT_ID = \"ваш_chat_id\""
echo ""
echo "📁 ФАЙЛИ ЛОГІВ:"
echo "   /home/gomoncli/api_monitor.log        - Автоматичні перевірки"
echo "   ./initial_api_report.txt              - Початковий звіт"
echo ""
echo "🔍 ЗАПУСТИТИ ПЕРШИЙ ТЕСТ:"
echo "   ./api_check.sh"
