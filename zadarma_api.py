# zadarma_api.py - Based on official GitHub implementation
import logging
import hashlib
import hmac
import base64
import requests
from urllib.parse import urlencode
from collections import OrderedDict
from config import (
    ZADARMA_API_KEY,
    ZADARMA_API_SECRET,
    ZADARMA_SIP_ACCOUNT,
    HVIRTKA_NUMBER,
    VOROTA_NUMBER,
    ADMIN_USER_ID,
    TELEGRAM_TOKEN
)

logger = logging.getLogger(__name__)

class ZadarmaAPI:
    def __init__(self, key, secret, is_sandbox=False):
        self.key = key
        self.secret = secret
        self.is_sandbox = is_sandbox
        self.__url_api = 'https://api.zadarma.com'
        if is_sandbox:
            self.__url_api = 'https://api-sandbox.zadarma.com'

    def call(self, method, params={}, request_type='GET', format='json', is_auth=True):
        """
        Function for send API request - точна копія з GitHub
        """
        logger.info(f"📡 Zadarma API call: {method}, params: {params}")
        
        request_type = request_type.upper()
        if request_type not in ['GET', 'POST', 'PUT', 'DELETE']:
            request_type = 'GET'
        
        params['format'] = format
        auth_str = None
        
        # Сортуємо параметри та створюємо query string
        params_string = urlencode(OrderedDict(sorted(params.items())))
        logger.info(f"🔐 Params string: {params_string}")

        if is_auth:
            auth_str = self.__get_auth_string_for_header(method, params_string)
            logger.info(f"🔐 Auth header: {auth_str}")

        url = self.__url_api + method
        logger.info(f"🌐 Request URL: {url}")

        if request_type == 'GET':
            if params_string:
                url += '?' + params_string
            result = requests.get(url, headers={'Authorization': auth_str})
        elif request_type == 'POST':
            result = requests.post(url, headers={'Authorization': auth_str}, data=params)
        elif request_type == 'PUT':
            result = requests.put(url, headers={'Authorization': auth_str}, data=params)
        elif request_type == 'DELETE':
            result = requests.delete(url, headers={'Authorization': auth_str}, data=params)

        logger.info(f"📡 Response status: {result.status_code}")
        logger.info(f"📡 Response: {result.text}")
        
        return result

    def __get_auth_string_for_header(self, method, params_string):
        """
        Офіційний алгоритм авторизації з GitHub
        """
        # Крок 1: створюємо рядок для підпису
        data = method + params_string + hashlib.md5(params_string.encode('utf8')).hexdigest()
        logger.info(f"🔐 String to sign: {data}")
        
        # Крок 2: HMAC SHA1
        hmac_h = hmac.new(self.secret.encode('utf8'), data.encode('utf8'), hashlib.sha1)
        
        # Крок 3: ВАЖЛИВО! Спочатку hexdigest, потім base64
        hex_digest = hmac_h.hexdigest()
        logger.info(f"🔐 HMAC hex digest: {hex_digest}")
        
        bts = bytes(hex_digest, 'utf8')
        signature = base64.b64encode(bts).decode()
        logger.info(f"🔐 Final signature: {signature}")
        
        # Крок 4: формуємо заголовок авторизації
        auth = self.key + ':' + signature
        return auth

# Глобальний екземпляр API
zadarma_api = ZadarmaAPI(ZADARMA_API_KEY, ZADARMA_API_SECRET)

def send_error_to_admin(message):
    """Відправляє повідомлення адміну"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": ADMIN_USER_ID, "text": message}
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"📤 Повідомлення адміну відправлено: {message}")
        else:
            logger.error(f"❌ Помилка відправки адміну (код {response.status_code})")
    except Exception as e:
        logger.error(f"❌ Помилка надсилання повідомлення адміну: {e}")

def make_zadarma_call(to_number: str) -> bool:
    """Робить callback дзвінок через офіційний API"""
    logger.info(f"📞 Робимо дзвінок на номер: {to_number}")
    
    # Імпортуємо функцію форматування
    from config import ZADARMA_MAIN_PHONE, format_phone_for_zadarma
    
    # Форматуємо номер призначення
    formatted_to = format_phone_for_zadarma(to_number)
    logger.info(f"📞 Відформатований номер TO: {formatted_to}")
    
    # Використовуємо основний номер який працює
    from_number = ZADARMA_MAIN_PHONE
    logger.info(f"📞 Використовуємо FROM номер: {from_number}")
    
    try:
        params = {
            "from": from_number,
            "to": formatted_to,
        }
        
        # Використовуємо офіційний API
        response = zadarma_api.call('/v1/request/callback/', params, 'GET')
        
        # Парсимо відповідь
        import json
        try:
            result = json.loads(response.text)
        except:
            result = {"status": "error", "message": f"Invalid JSON: {response.text}"}
        
        if result.get("status") == "success":
            logger.info(f"✅ Успішний дзвінок з {from_number} на {formatted_to}")
            logger.info(f"📋 Повна відповідь: {result}")
            return True
        else:
            error_msg = result.get("message", "Unknown error")
            logger.warning(f"❌ Помилка дзвінка: {error_msg}")
            return False
            
    except Exception as e:
        logger.exception(f"❌ Помилка виклику API: {e}")
        return False

def test_phone_formats():
    """Тестує різні формати номерів для Zadarma API"""
    logger.info("🧪 Тестування форматів номерів...")
    
    test_numbers = [
        "380933297777",
        "+380933297777", 
        "0933297777",
        "933297777"
    ]
    
    from config import format_phone_for_zadarma
    
    for number in test_numbers:
        formatted = format_phone_for_zadarma(number)
        logger.info(f"📞 {number} → {formatted}")
    
    return True

def test_zadarma_auth():
    """Тестуємо базову авторизацію"""
    logger.info("🧪 Тестування авторизації з офіційним API...")
    
    try:
        response = zadarma_api.call('/v1/sip/', {}, 'GET')
        
        import json
        result = json.loads(response.text)
        
        if result.get("status") == "success":
            logger.info(f"✅ Авторизація працює: {result}")
            return True
        else:
            logger.error(f"❌ Авторизація не працює: {result}")
            return False
            
    except Exception as e:
        logger.exception(f"❌ Помилка тестування авторизації: {e}")
        return False

def check_zadarma_sip():
    """Перевірка SIP статусу"""
    logger.info("🔍 Перевірка Zadarma SIP...")
    
    try:
        if not test_zadarma_auth():
            raise Exception("Базова авторизація не працює")
        
        response = zadarma_api.call('/v1/sip/', {}, 'GET')
        result = json.loads(response.text)
        
        if result.get("status") != "success":
            raise Exception(f"Zadarma SIP status not success: {result}")
            
        logger.info("✅ Zadarma SIP перевірка пройшла успішно")
        logger.info(f"📋 SIP інформація: {result}")
        
    except Exception as e:
        logger.exception(f"❌ Помилка перевірки Zadarma SIP: {e}")
        send_error_to_admin(f"❗️ Помилка авторизації Zadarma SIP: {e}")
        raise

# Для сумісності зі старим кодом
def make_zadarma_call_handler(target_number, label):
    def handler(bot, update):
        user_id = update.message.chat_id
        logger.info(f"🔑 Викликано {label} для користувача {user_id}")
        
        try:
            bot.send_message(chat_id=user_id, text="🔑 Підбираємо ключі...")
            success = make_zadarma_call(target_number)
            
            if success:
                bot.send_message(chat_id=user_id, text=f"✅ {label} буде відчинено за кілька секунд.")
                logger.info(f"✅ {label} успішно активовано для {user_id}")
            else:
                raise Exception("Zadarma API call returned unsuccessful result.")
                
        except Exception as e:
            logger.exception(f"❌ Помилка при виклику {label}: {e}")
            bot.send_message(chat_id=user_id, text="⚠️ Сталася помилка, спробуйте, будь ласка, ще раз, або зателефонуйте нам за номером 073-310-31-10")
            send_error_to_admin(f"❗️ Помилка при виклику Zadarma ({label}): {e}")
            
    return handler

# Окремі хендлери
handle_gate_command = make_zadarma_call_handler(VOROTA_NUMBER, "Ворота")
handle_door_command = make_zadarma_call_handler(HVIRTKA_NUMBER, "Хвіртку")