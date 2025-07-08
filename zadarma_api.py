import logging
from config import ZADARMA_API_KEY, ZADARMA_API_SECRET, ZADARMA_SIP_ACCOUNT
from user_api.zadarma.api import ZadarmaAPI

logger = logging.getLogger("zadarma_api")
zadarma = ZadarmaAPI(ZADARMA_API_KEY, ZADARMA_API_SECRET)

def make_zadarma_call(to_number):
    try:
        params = {
            'from': f'sip{ZADARMA_SIP_ACCOUNT}',  # ← тут виправлено
            'to': to_number,
            'voice_start': 'continue'
        }
        response = zadarma.call('/v1/request/callback/', params, request_type='GET')
        logger.info(f"Виконано дзвінок Zadarma: {response}")
        return response
    except Exception as e:
        logger.error(f"Помилка дзвінка: {e}")
        return f"Помилка: {e}"

def make_zadarma_call_handler(to_number):
    def handler(bot, update):
        bot.send_message(chat_id=update.effective_chat.id, text="Ініціюю дзвінок...")
        result = make_zadarma_call(to_number)
        bot.send_message(chat_id=update.effective_chat.id, text=f"Результат дзвінка:\n{result}")
    return handler

def get_my_sip_info():
    try:
        response = zadarma.call('/v1/sip/')
        logger.info(f"Інформація про SIP-номери: {response}")
        return response
    except Exception as e:
        logger.error(f"Помилка отримання інформації про номер: {e}")
        return str(e)
