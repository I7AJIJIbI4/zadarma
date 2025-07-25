# zadarma_call.py - Production version with official API
import logging
from telegram import ChatAction
from zadarma_api import make_zadarma_call
from config import HVIRTKA_NUMBER, VOROTA_NUMBER

logger = logging.getLogger(__name__)

def handle_gate_command(bot, update):
    """Обробник команди відкриття воріт"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    logger.info(f"🚪 /vorota викликано користувачем: {user_id} (@{username})")
    
    # 🔒 ПЕРЕВІРКА АВТОРИЗАЦІЇ
    from user_db import is_authorized_user_simple
    
    if not is_authorized_user_simple(user_id):
        bot.send_message(
            chat_id=chat_id,
            text="❌ Доступ заборонено! Спочатку авторизуйтеся через /start"
        )
        logger.warning(f"❌ НЕАВТОРИЗОВАНИЙ користувач {user_id} спробував відкрити ворота!")
        return
    
    try:
        # Показуємо що бот "друкує"
        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # Повідомляємо користувача
        bot.send_message(chat_id=chat_id, text="🔑 Підбираємо ключі…")
        
        logger.info(f"📞 Викликаємо Zadarma для воріт: {VOROTA_NUMBER}")
        
        # Використовуємо новий оптимізований API
        success = make_zadarma_call(VOROTA_NUMBER)
        
        if success:
            logger.info(f"✅ Ворота успішно відкрито для користувача {user_id}")
            bot.send_message(
                chat_id=chat_id, 
                text="✅ Ворота буде відчинено за кілька секунд."
            )
        else:
            logger.warning(f"❌ Не вдалося відкрити ворота для користувача {user_id}")
            bot.send_message(
                chat_id=chat_id, 
                text="❌ Сталася помилка, спробуйте, будь ласка, ще раз, або зателефонуйте нам за номером 073-310-31-10"
            )
            
    except Exception as e:
        logger.exception(f"❌ Помилка при відкритті воріт для користувача {user_id}: {e}")
        bot.send_message(
            chat_id=chat_id, 
            text="❌ Сталася помилка, спробуйте, будь ласка, ще раз, або зателефонуйте нам за номером 073-310-31-10"
        )

def handle_door_command(bot, update):
    """Обробник команди відкриття хвіртки"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    logger.info(f"🚪 /hvirtka викликано користувачем: {user_id} (@{username})")
    
    # 🔒 ПЕРЕВІРКА АВТОРИЗАЦІЇ
    from user_db import is_authorized_user_simple
    
    if not is_authorized_user_simple(user_id):
        bot.send_message(
            chat_id=chat_id,
            text="❌ Доступ заборонено! Спочатку авторизуйтеся через /start"
        )
        logger.warning(f"❌ НЕАВТОРИЗОВАНИЙ користувач {user_id} спробував відкрити хвіртку!")
        return
    
    try:
        # Показуємо що бот "друкує"
        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # Повідомляємо користувача
        bot.send_message(chat_id=chat_id, text="🔑 Підбираємо ключі…")
        
        logger.info(f"📞 Викликаємо Zadarma для хвіртки: {HVIRTKA_NUMBER}")
        
        # Використовуємо новий оптимізований API
        success = make_zadarma_call(HVIRTKA_NUMBER)
        
        if success:
            logger.info(f"✅ Хвіртка успішно відкрита для користувача {user_id}")
            bot.send_message(
                chat_id=chat_id, 
                text="✅ Хвіртку буде відчинено за кілька секунд."
            )
        else:
            logger.warning(f"❌ Не вдалося відкрити хвіртку для користувача {user_id}")
            bot.send_message(
                chat_id=chat_id, 
                text="❌ Сталася помилка, спробуйте, будь ласка, ще раз, або зателефонуйте нам за номером 073-310-31-10"
            )
            
    except Exception as e:
        logger.exception(f"❌ Помилка при відкритті хвіртки для користувача {user_id}: {e}")
        bot.send_message(
            chat_id=chat_id, 
            text="❌ Сталася помилка, спробуйте, будь ласка, ще раз, або зателефонуйте нам за номером 073-310-31-10"
        )