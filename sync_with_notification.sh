#!/bin/bash
# Скрипт синхронізації з Telegram повідомленням

LOG_FILE="/home/gomoncli/zadarma/sync_notification.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] 🔄 Запуск синхронізації з повідомленням..." >> $LOG_FILE

cd /home/gomoncli/zadarma/

# Запускаємо синхронізацію і захоплюємо результат
python3 -c "
import sys
sys.path.append('/home/gomoncli/zadarma')

from sync_clients import sync_clients
from config import TELEGRAM_TOKEN, ADMIN_USER_ID
import requests
import logging
from datetime import datetime

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {
        'chat_id': ADMIN_USER_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            logger.info('📱 Telegram повідомлення відправлено')
            return True
        else:
            logger.error(f'❌ Помилка Telegram API: {response.status_code}')
            return False
    except Exception as e:
        logger.error(f'❌ Помилка відправки Telegram: {e}')
        return False

try:
    logger.info('🔄 Запуск синхронізації клієнтів...')
    
    # Запускаємо синхронізацію
    result = sync_clients()
    
    # Формуємо повідомлення
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if result:
        message = f'''📊 <b>ЗВІТ СИНХРОНІЗАЦІЇ КЛІЄНТІВ</b>
        
🕐 Час: {now}
✅ Статус: Завершено успішно
🔄 Тип: Автоматичне оновлення
📅 Період: Остання доба

ℹ️ Детальна інформація в логах системи'''
    else:
        message = f'''📊 <b>ЗВІТ СИНХРОНІЗАЦІЇ КЛІЄНТІВ</b>
        
🕐 Час: {now}
⚠️ Статус: Завершено з попередженнями
🔄 Тип: Автоматичне оновлення

⚠️ Перевірте логи системи для деталей'''
    
    # Відправляємо повідомлення
    send_telegram_message(message)
    logger.info('✅ Синхронізація та повідомлення завершено')
    
except Exception as e:
    logger.error(f'❌ Помилка синхронізації: {e}')
    
    # Відправляємо повідомлення про помилку
    error_message = f'''📊 <b>ПОМИЛКА СИНХРОНІЗАЦІЇ</b>
    
🕐 Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
❌ Статус: Помилка
🔧 Деталі: {str(e)}

🛠️ Потрібна перевірка системи'''
    
    send_telegram_message(error_message)
" >> $LOG_FILE 2>&1

echo "[$DATE] ✅ Синхронізація завершена" >> $LOG_FILE
