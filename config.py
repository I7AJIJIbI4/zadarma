

# config.py

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

# Номери для викликів
HVIRTKA_NUMBER = "0933297777"  # приклад: +380991234567
VOROTA_NUMBER = "0930063585"   # приклад: +380991234568

# URLs для бота
MAP_URL = "https://maps.app.goo.gl/vf1EzwWPNdCqZDvx9"
SCHEME_URL = "https://ibb.co/6JZ9VHw"
SUPPORT_PHONE = "073-310-31-10"

def format_phone_for_zadarma(phone):
    """
    Конвертує номер телефону в формат який працює з Zadarma API
    """
    # Видаляємо всі не-цифрові символи
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    # Якщо номер починається з 380, конвертуємо в формат 0XXXXXXXXX
    if clean_phone.startswith('380'):
        return '0' + clean_phone[3:]
    
    # Якщо номер не починається з 0, додаємо 0
    elif len(clean_phone) == 9:
        return '0' + clean_phone
    
    # Якщо номер вже у правильному форматі 0XXXXXXXXX
    elif len(clean_phone) == 10 and clean_phone.startswith('0'):
        return clean_phone
    
    # Інакше повертаємо як є
    return clean_phone


