# zadarma_api.py - Enhanced version with call status tracking
import logging
import hashlib
import hmac
import base64
import requests
import json
import time
import threading
from urllib.parse import urlencode
from collections import OrderedDict
from datetime import datetime
from config import (
    ZADARMA_API_KEY,
    ZADARMA_API_SECRET,
    ZADARMA_MAIN_PHONE,
    ADMIN_USER_ID,
    TELEGRAM_TOKEN,
    format_phone_for_zadarma,
    validate_phone_number
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

        try:
            if request_type == 'GET':
                if params_string:
                    url += '?' + params_string
                result = requests.get(url, headers={'Authorization': auth_str}, timeout=10)
            elif request_type == 'POST':
                result = requests.post(url, headers={'Authorization': auth_str}, data=params, timeout=10)
            elif request_type == 'PUT':
                result = requests.put(url, headers={'Authorization': auth_str}, data=params, timeout=10)
            elif request_type == 'DELETE':
                result = requests.delete(url, headers={'Authorization': auth_str}, data=params, timeout=10)

            logger.info(f"📡 Response status: {result.status_code}")
            logger.info(f"📡 Response: {result.text}")
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error("❌ Таймаут запиту до Zadarma API")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Помилка запиту до Zadarma API: {e}")
            raise

    def __get_auth_string_for_header(self, method, params_string):
        """
        Офіційний алгоритм авторизації з GitHub
        """
        # Крок 1: створюємо рядок для підпису
        data = method + params_string + hashlib.md5(params_string.encode('utf8')).hexdigest()
        logger.debug(f"🔐 String to sign: {data}")
        
        # Крок 2: HMAC SHA1
        hmac_h = hmac.new(self.secret.encode('utf8'), data.encode('utf8'), hashlib.sha1)
        
        # Крок 3: ВАЖЛИВО! Спочатку hexdigest, потім base64
        hex_digest = hmac_h.hexdigest()
        logger.debug(f"🔐 HMAC hex digest: {hex_digest}")
        
        bts = bytes(hex_digest, 'utf8')
        signature = base64.b64encode(bts).decode()
        logger.debug(f"🔐 Final signature: {signature}")
        
        # Крок 4: формуємо заголовок авторизації
        auth = self.key + ':' + signature
        return auth

# Глобальний екземпляр API
zadarma_api = ZadarmaAPI(ZADARMA_API_KEY, ZADARMA_API_SECRET)

class CallStatusTracker:
    """Клас для відстеження статусу дзвінків"""
    
    def __init__(self):
        self.active_calls = {}
        self.call_history = []
        
    def register_call(self, call_id, user_id, chat_id, action_type, target_number):
        """Реєструє новий дзвінок для відстеження"""
        call_info = {
            'call_id': call_id,
            'user_id': user_id,
            'chat_id': chat_id,
            'action_type': action_type,  # 'hvirtka' або 'vorota'
            'target_number': target_number,
            'start_time': time.time(),
            'status': 'initiated'
        }
        
        self.active_calls[call_id] = call_info
        logger.info(f"📋 Зареєстровано дзвінок для відстеження: {call_id}")
        
        # Запускаємо моніторинг в окремому потоці
        thread = threading.Thread(target=self._monitor_call, args=(call_id,))
        thread.daemon = True
        thread.start()
        
    def _monitor_call(self, call_id):
        """Моніторить статус конкретного дзвінка"""
        if call_id not in self.active_calls:
            logger.warning(f"⚠️ Дзвінок {call_id} не знайдено для моніторингу")
            return
            
        call_info = self.active_calls[call_id]
        max_wait_time = 30  # 30 секунд максимум
        check_interval = 3   # Перевіряти кожні 3 секунди
        
        logger.info(f"🔍 Почато моніторинг дзвінка {call_id}")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # Отримуємо статистику дзвінка
                response = zadarma_api.call(f'/v1/statistics/', 
                                          {'start': call_info['start_time'], 'end': time.time()}, 
                                          'GET')
                result = json.loads(response.text)
                
                if result.get('status') == 'success':
                    # Шукаємо наш дзвінок в статистиці
                    calls = result.get('calls', [])
                    our_call = None
                    
                    for call in calls:
                        if (call.get('to') == call_info['target_number'] and 
                            call.get('from') == ZADARMA_MAIN_PHONE):
                            our_call = call
                            break
                    
                    if our_call:
                        disposition = our_call.get('disposition', '')
                        call_status = our_call.get('status', '')
                        
                        logger.info(f"📞 Статус дзвінка {call_id}: {call_status}, disposition: {disposition}")
                        
                        if disposition == 'rejected':
                            # ✅ УСПІХ: Дзвінок скинуто після гудків - ворота/хвіртка відкриються!
                            self._handle_call_rejected(call_id)
                            return
                        elif disposition in ['busy', 'failed', 'no-answer', 'cancel']:
                            # ❌ НЕВДАЧА: Дзвінок не дійшов або номер зайнятий
                            self._handle_call_failed(call_id, disposition)
                            return
                        elif disposition == 'answered':
                            # ⚠️ ПРОБЛЕМА: Дзвінок прийнято замість скидання - система працює неправильно
                            self._handle_call_answered(call_id)
                            return
                
            except Exception as e:
                logger.error(f"❌ Помилка перевірки статусу дзвінка {call_id}: {e}")
            
            time.sleep(check_interval)
        
        # Таймаут - статус невизначений
        self._handle_call_timeout(call_id)
        
    def _handle_call_rejected(self, call_id):
        """Обробляє успішно скинутий дзвінок - ЦЕ УСПІХ!"""
        call_info = self.active_calls.get(call_id)
        if not call_info:
            return
            
        logger.info(f"✅ Дзвінок {call_id} скинуто після гудків - {call_info['action_type']} буде відкрито!")
        
        # Відправляємо повідомлення про успішне відкриття
        action_name = "хвіртку" if call_info['action_type'] == 'hvirtka' else "ворота"
        success_message = f"✅ {action_name.capitalize()} буде відчинено за кілька секунд."
        
        send_telegram_message(call_info['chat_id'], success_message)
        
        # Переносимо в історію та видаляємо з активних
        call_info['status'] = 'success'
        call_info['disposition'] = 'rejected'
        call_info['end_time'] = time.time()
        self.call_history.append(call_info)
        del self.active_calls[call_id]
        
    def _handle_call_failed(self, call_id, disposition):
        """Обробляє невдалий дзвінок - ворота НЕ відкриються"""
        call_info = self.active_calls.get(call_id)
        if not call_info:
            return
            
        logger.warning(f"❌ Дзвінок {call_id} не вдався: {disposition} - ворота НЕ відкриються")
        
        action_name = "хвіртку" if call_info['action_type'] == 'hvirtka' else "ворота"
        
        # Різні повідомлення залежно від типу помилки
        if disposition == 'busy':
            error_message = f"❌ Номер {action_name} зайнятий. Спробуйте ще раз через хвилину."
        elif disposition == 'no-answer':
            error_message = f"❌ Номер {action_name} не відповідає. Можливо проблеми зв'язку."
        elif disposition == 'failed':
            error_message = f"❌ Дзвінок на {action_name} не пройшов. Проблеми зв'язку."
        else:
            error_message = f"❌ Не вдалося відкрити {action_name}. Причина: {disposition}"
        
        error_message += f"\n\nСпробуйте ще раз або зателефонуйте нам за номером <a href=\"tel:+380733103110\">+380733103110</a>"
        
        send_telegram_message(call_info['chat_id'], error_message)
        
        # Переносимо в історію
        call_info['status'] = 'failed'
        call_info['disposition'] = disposition
        call_info['end_time'] = time.time()
        self.call_history.append(call_info)
        del self.active_calls[call_id]
        
    def _handle_call_answered(self, call_id):
        """Обробляє прийнятий дзвінок - це ПРОБЛЕМА в налаштуваннях!"""
        call_info = self.active_calls.get(call_id)
        if not call_info:
            return
            
        logger.error(f"⚠️ ПРОБЛЕМА: Дзвінок {call_id} було ПРИЙНЯТО замість скидання!")
        
        action_name = "хвіртку" if call_info['action_type'] == 'hvirtka' else "ворота"
        warning_message = (
            f"⚠️ Дзвінок для відкриття {action_name} було прийнято.\n"
            f"Можливо, система не налаштована правильно.\n\n"
            f"Зверніться до підтримки: <a href=\"tel:+380733103110\">+380733103110</a>"
        )
        
        send_telegram_message(call_info['chat_id'], warning_message)
        
        # Сповіщаємо адміна про проблему в налаштуваннях
        admin_alert = f"🚨 ПРОБЛЕМА НАЛАШТУВАННЯ: Дзвінок на {action_name} ({call_info['target_number']}) було ПРИЙНЯТО замість скидання! Перевірте налаштування пристрою."
        send_telegram_message(ADMIN_USER_ID, admin_alert)
        
        # Переносимо в історію
        call_info['status'] = 'answered'
        call_info['disposition'] = 'answered'
        call_info['end_time'] = time.time()
        self.call_history.append(call_info)
        del self.active_calls[call_id]
        
    def _handle_call_timeout(self, call_id):
        """Обробляє таймаут перевірки статусу - невизначений результат"""
        call_info = self.active_calls.get(call_id)
        if not call_info:
            return
            
        logger.warning(f"⏰ Таймаут моніторингу дзвінка {call_id} - статус невизначений")
        
        action_name = "хвіртку" if call_info['action_type'] == 'hvirtka' else "ворота"
        timeout_message = (
            f"⏰ Статус відкриття {action_name} не визначено.\n"
            f"Спробуйте ще раз або перевірте фізично.\n\n"
            f"При проблемах телефонуйте: <a href=\"tel:+380733103110\">+380733103110</a>"
        )
        
        send_telegram_message(call_info['chat_id'], timeout_message)
        
        # Переносимо в історію
        call_info['status'] = 'timeout'
        call_info['end_time'] = time.time()
        self.call_history.append(call_info)
        del self.active_calls[call_id]

# Глобальний трекер статусу дзвінків
call_tracker = CallStatusTracker()

def send_telegram_message(chat_id, message):
    """Відправляє повідомлення в Telegram з HTML форматуванням"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"📤 Повідомлення відправлено в чат {chat_id}")
        else:
            logger.error(f"❌ Помилка відправки повідомлення (код {response.status_code})")
    except Exception as e:
        logger.error(f"❌ Помилка надсилання повідомлення: {e}")

def send_error_to_admin(message):
    """Відправляє повідомлення про помилку адміну"""
    send_telegram_message(ADMIN_USER_ID, f"🔧 ADMIN: {message}")

def make_zadarma_call_with_tracking(to_number: str, user_id: int, chat_id: int, action_type: str) -> dict:
    """
    Робить callback дзвінок через API з відстеженням статусу
    
    Args:
        to_number: номер для дзвінка
        user_id: ID користувача Telegram
        chat_id: ID чату для повідомлень
        action_type: 'hvirtka' або 'vorota'
        
    Returns:
        dict: результат з полями success, call_id, message
    """
    logger.info(f"📞 Робимо дзвінок з відстеженням на номер: {to_number}")
    
    # Валідація номеру
    if not validate_phone_number(to_number):
        error_msg = f"Неправильний формат номеру: {to_number}"
        logger.error(f"❌ {error_msg}")
        return {"success": False, "message": error_msg}
    
    # Форматуємо номер призначення
    formatted_to = format_phone_for_zadarma(to_number)
    logger.info(f"📞 Відформатований номер TO: {formatted_to}")
    
    # Використовуємо основний номер
    from_number = ZADARMA_MAIN_PHONE
    logger.info(f"📞 Використовуємо FROM номер: {from_number}")
    
    try:
        params = {
            "from": from_number,
            "to": formatted_to,
        }
        
        # Робимо API запит
        response = zadarma_api.call('/v1/request/callback/', params, 'GET')
        
        # Парсимо відповідь
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            error_msg = f"Некоректна відповідь API: {response.text}"
            logger.error(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
        
        logger.info("🔍 CRITICAL: Before status check in zadarma_api.py")
        logger.info("🔍 CRITICAL: result content: " + str(result))
        if result.get("status") == "success":
            logger.info(f"✅ Успішний запит дзвінка з {from_number} на {formatted_to}")
            logger.info(f"📋 Повна відповідь: {result}")
            
            # Генеруємо унікальний ID для відстеження
            # (Zadarma не завжди повертає call_id в callback API)
            call_id = f"{user_id}_{int(time.time())}"
            
            # Реєструємо дзвінок для відстеження
            call_tracker.register_call(call_id, user_id, chat_id, action_type, formatted_to)
            
            return {
                "success": True, 
                "call_id": call_id,
                "message": "Дзвінок ініційовано, очікуємо результат..."
            }
        else:
            error_msg = result.get("message", "Невідома помилка API")
            logger.warning(f"❌ Помилка API дзвінка: {error_msg}")
            return {"success": False, "message": error_msg}
            
    except Exception as e:
        error_msg = f"Помилка виклику API: {str(e)}"
        logger.exception(f"❌ {error_msg}")
        return {"success": False, "message": error_msg}

def make_zadarma_call(to_number: str) -> bool:
    """
    Стара функція для зворотної сумісності
    Робить дзвінок без відстеження статусу
    """
    result = make_zadarma_call_with_tracking(to_number, 0, 0, "legacy")
    return result["success"]

# Функції для тестування та діагностики
def test_zadarma_auth():
    """Тестуємо базову авторизацію"""
    logger.info("🧪 Тестування авторизації з офіційним API...")
    
    try:
        response = zadarma_api.call('/v1/info/balance/', {}, 'GET')
        result = json.loads(response.text)
        
        if result.get("status") == "success":
            balance = result.get("balance", "невідомо")
            currency = result.get("currency", "")
            logger.info(f"✅ Авторизація працює. Баланс: {balance} {currency}")
            return True
        else:
            logger.error(f"❌ Авторизація не працює: {result}")
            return False
            
    except Exception as e:
        logger.exception(f"❌ Помилка тестування авторизації: {e}")
        return False

def get_call_statistics(hours=24):
    """Отримує статистику дзвінків за останні години"""
    try:
        end_time = time.time()
        start_time = end_time - (hours * 3600)
        
        params = {
            'start': int(start_time),
            'end': int(end_time)
        }
        
        response = zadarma_api.call('/v1/statistics/', params, 'GET')
        result = json.loads(response.text)
        
        if result.get("status") == "success":
            calls = result.get('calls', [])
            logger.info(f"📊 Отримано статистику: {len(calls)} дзвінків за {hours} годин")
            return calls
        else:
            logger.error(f"❌ Помилка отримання статистики: {result}")
            return []
            
    except Exception as e:
        logger.exception(f"❌ Помилка отримання статистики дзвінків: {e}")
        return []

def cleanup_old_calls():
    """Очищає стару історію дзвінків (залишає тільки останні 100)"""
    if len(call_tracker.call_history) > 100:
        old_count = len(call_tracker.call_history) - 100
        call_tracker.call_history = call_tracker.call_history[-100:]
        logger.info(f"🧹 Очищено {old_count} старих записів дзвінків")

# Запуск очищення кожні 6 годин
def start_cleanup_scheduler():
    """Запускає періодичне очищення"""
    import threading
    
    def cleanup_loop():
        while True:
            time.sleep(6 * 3600)  # 6 годин
            cleanup_old_calls()
    
    thread = threading.Thread(target=cleanup_loop)
    thread.daemon = True
    thread.start()
    logger.info("🔄 Запущено автоочищення історії дзвінків")

# Ініціалізація при імпорті
if __name__ != "__main__":
    start_cleanup_scheduler()
