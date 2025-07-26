# config.py - Fixed version with proper validation

import logging
import re

logger = logging.getLogger(__name__)

# Telegram
TELEGRAM_TOKEN = "8030228734:AAGYMKVWYfNT5h-UJlVWmmWmul8-KhdaOk4"
ADMIN_USER_ID = 573368771  # Твій Telegram user_id

# Zadarma API
ZADARMA_API_KEY = "322168f1b94be856f0de"
ZADARMA_API_SECRET = "ae4b189367a9f6de88b3"
ZADARMA_SIP_ACCOUNT = "107122"  # наприклад: 107122 або +380733103110
ZADARMA_MAIN_PHONE = "0733103110"

# Wlaunch API
WLAUNCH_API_KEY = "d5_Js-ZJX_8bJxCxg2ekWTV0Z8c"
COMPANY_ID = "3f3027ca-0b21-11ed-8355-65920565acdd"

# Шлях до БД
DB_PATH = "/home/gomoncli/zadarma/users.db"

<<<<<<< Updated upstream
# Номери для викликів - ВИПРАВЛЕНО на основі логів
HVIRTKA_NUMBER = "0637442017"  # Реальний номер з логів
VOROTA_NUMBER = "0930063585"   # Залишаємо як було
=======
# Номери для викликів
HVIRTKA_NUMBER = "0637442017"  # приклад: +380991234567
VOROTA_NUMBER = "0930063585"   # приклад: +380991234568
>>>>>>> Stashed changes

# URLs для бота
MAP_URL = "https://maps.app.goo.gl/vf1EzwWPNdCqZDvx9"
SCHEME_URL = "https://ibb.co/6JZ9VHw"
SUPPORT_PHONE = "0733103110"

def format_phone_for_zadarma(phone):
    """
    Покращена функція конвертації номеру телефону в формат Zadarma API
    Підтримує різні вхідні формати та логує процес для діагностики
    
    Args:
        phone (str): Вхідний номер у будь-якому форматі
        
    Returns:
        str: Номер у форматі 0XXXXXXXXX для Zadarma API
        
    Examples:
        "+380991234567" -> "0991234567"
        "380991234567" -> "0991234567" 
        "0991234567" -> "0991234567"
        "991234567" -> "0991234567"
    """
    logger.debug(f"📞 Форматування номеру: вхід = '{phone}'")
    
    # Видаляємо всі символи крім цифр
    clean_phone = re.sub(r'\D', '', phone)
    logger.debug(f"📞 Після очищення: '{clean_phone}'")
    
    # Правила конвертації
    if clean_phone.startswith('380'):
        # +380XXXXXXXXX або 380XXXXXXXXX -> 0XXXXXXXXX
        if len(clean_phone) == 12:  # 380 + 9 цифр
            result = '0' + clean_phone[3:]
        else:
            logger.warning(f"⚠️ Незвична довжина номеру з 380: {len(clean_phone)}")
            result = clean_phone
            
    elif len(clean_phone) == 9:
        # XXXXXXXXX -> 0XXXXXXXXX (додаємо 0 на початок)
        result = '0' + clean_phone
        
    elif len(clean_phone) == 10 and clean_phone.startswith('0'):
        # 0XXXXXXXXX -> залишаємо без змін (правильний формат)
        result = clean_phone
        
    elif len(clean_phone) == 10 and not clean_phone.startswith('0'):
        # Номер з 10 цифр але не починається з 0 - можливо помилка
        logger.warning(f"⚠️ Номер з 10 цифр не починається з 0: {clean_phone}")
        result = clean_phone
        
    else:
        # Інші випадки - залишаємо як є але логуємо попередження
        logger.warning(f"⚠️ Незвичний формат номеру: {phone} -> {clean_phone} (довжина: {len(clean_phone)})")
        result = clean_phone
    
    # Валідація результату
    if len(result) != 10:
        logger.error(f"❌ ПОМИЛКА: результат має неправильну довжину: '{result}' (довжина: {len(result)})")
    elif not result.startswith('0'):
        logger.warning(f"⚠️ УВАГА: результат не починається з 0: '{result}'")
    
    logger.info(f"📞 Фінальне форматування: '{phone}' -> '{result}'")
    return result

def validate_phone_number(phone):
    """
    Валідує номер телефону для Zadarma API
    
    Args:
        phone (str): Номер для перевірки
        
    Returns:
        bool: True якщо номер валідний
    """
    if not phone:
        return False
        
    # Номер має бути рівно 10 цифр і починатися з 0
    if len(phone) != 10:
        return False
        
    if not phone.startswith('0'):
        return False
        
    if not phone.isdigit():
        return False
        
    return True

def validate_config():
    """
    Валідує конфігурацію при запуску додатку
    Перевіряє що всі критичні налаштування правильні
    """
    errors = []
    
    # Перевірка номерів
    if not validate_phone_number(HVIRTKA_NUMBER):
        errors.append(f"Неправильний формат HVIRTKA_NUMBER: '{HVIRTKA_NUMBER}' (має бути 0XXXXXXXXX)")
        
    if not validate_phone_number(VOROTA_NUMBER):
        errors.append(f"Неправильний формат VOROTA_NUMBER: '{VOROTA_NUMBER}' (має бути 0XXXXXXXXX)")
        
    if not validate_phone_number(ZADARMA_MAIN_PHONE):
        errors.append(f"Неправильний формат ZADARMA_MAIN_PHONE: '{ZADARMA_MAIN_PHONE}' (має бути 0XXXXXXXXX)")
    
    # Перевірка API ключів
    if not ZADARMA_API_KEY or len(ZADARMA_API_KEY) < 10:
        errors.append("Відсутній або некоректний ZADARMA_API_KEY")
        
    if not ZADARMA_API_SECRET or len(ZADARMA_API_SECRET) < 10:
        errors.append("Відсутній або некоректний ZADARMA_API_SECRET")
        
    if not TELEGRAM_TOKEN or len(TELEGRAM_TOKEN) < 20:
        errors.append("Відсутній або некоректний TELEGRAM_TOKEN")
    
    # Перевірка шляхів
    import os
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        errors.append(f"Директорія для БД не існує: {db_dir}")
    
    if errors:
        error_msg = "❌ ПОМИЛКИ КОНФІГУРАЦІЇ:\n" + "\n".join(f"  • {error}" for error in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)
    else:
        logger.info("✅ Конфігурація пройшла валідацію")
        logger.info(f"📞 HVIRTKA_NUMBER: {HVIRTKA_NUMBER}")
        logger.info(f"🚪 VOROTA_NUMBER: {VOROTA_NUMBER}")
        logger.info(f"📱 ZADARMA_MAIN_PHONE: {ZADARMA_MAIN_PHONE}")

# Тестові функції
def test_phone_formatting():
    """Тестує функцію форматування номерів"""
    test_cases = [
        ("+380991234567", "0991234567"),
        ("380991234567", "0991234567"),
        ("0991234567", "0991234567"),
        ("991234567", "0991234567"),
        ("+380 99 123 45 67", "0991234567"),
        ("38(099)123-45-67", "0991234567"),
    ]
    
    logger.info("🧪 Тестування форматування номерів...")
    
    for input_phone, expected in test_cases:
        result = format_phone_for_zadarma(input_phone)
        status = "✅" if result == expected else "❌"
        logger.info(f"{status} '{input_phone}' -> '{result}' (очікується: '{expected}')")
        
        if result != expected:
            logger.error(f"❌ ТЕСТ НЕ ПРОЙШОВ: {input_phone} -> {result}, очікувалося {expected}")

if __name__ == "__main__":
    # Якщо файл запускається напряму - тестуємо
    logging.basicConfig(level=logging.INFO)
    test_phone_formatting()
    validate_config()
