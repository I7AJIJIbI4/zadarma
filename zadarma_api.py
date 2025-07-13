import logging
from config import ZADARMA_API_KEY, ZADARMA_API_SECRET, ZADARMA_SIP_ACCOUNT
from user_api.zadarma.api import ZadarmaAPI

zadarma = ZadarmaAPI(ZADARMA_API_KEY, ZADARMA_API_SECRET)
logger = logging.getLogger("zadarma_api")

def make_zadarma_call(to_number):
    try:
        params = {
            'from': ZADARMA_SIP_ACCOUNT,
            'to': to_number,
            'voice_start': 'continue'
        }
        response = zadarma.call('/v1/request/callback/', params, request_type='GET')
        if '"status":"success"' in response:
            logger.info(f"Успішний дзвінок до {to_number}")
            return "success"
        else:
            logger.error(f"Помилка дзвінка: {response}")
            return "failed"
    except Exception as e:
        logger.error(f"Виняток під час дзвінка: {e}")
        return "failed"

# 🧩 Це і є твоя фабрика хендлерів
def make_zadarma_call_handler(to_number):
    def handler(bot, update):
        bot.send_message(chat_id=update.effective_chat.id, text="Виконую дзвінок...")
        result = make_zadarma_call(to_number)
        bot.send_message(chat_id=update.effective_chat.id, text=f"Статус: {result}")
    return handler

def get_my_sip_info():
    try:
        response = zadarma.call('/v1/sip/')
        logger.info(f"Інформація про номер: {response}")
        return response
    except Exception as e:
        logger.error(f"Помилка отримання інформації про номер: {e}")
        return "failed"
