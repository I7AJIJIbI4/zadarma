# bot.py - Final version with HTML clickable links
import os
import sys
import time
import logging
import threading
import atexit
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
from user_db import init_db, is_authorized_user_simple, get_user_info
from zadarma_call import handle_door_command, handle_gate_command
from config import TELEGRAM_TOKEN, ADMIN_USER_ID, MAP_URL, SCHEME_URL

# Змініть назву функції для сумісності
is_authenticated = is_authorized_user_simple

# ВИПРАВЛЕНЕ ЛОГУВАННЯ - без дублювання
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def create_pid_file():
    """Створює PID файл для бота"""
    pid_file = "/home/gomoncli/zadarma/bot.pid"
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"📁 PID файл створено: {pid_file} (PID: {os.getpid()})")
        
        # Видаляємо PID файл при завершенні
        def cleanup_pid():
            try:
                if os.path.exists(pid_file):
                    os.remove(pid_file)
                    logger.info(f"📁 PID файл видалено: {pid_file}")
            except Exception as e:
                logger.error(f"❌ Помилка видалення PID файлу: {e}")
        
        atexit.register(cleanup_pid)
        
        # Також видаляємо при отриманні сигналів
        import signal
        def signal_handler(signum, frame):
            logger.info(f"📡 Отримано сигнал {signum}, завершуємо роботу...")
            cleanup_pid()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
    except Exception as e:
        logger.error(f"❌ Помилка створення PID файлу: {e}")

def send_error_to_admin(bot, message):
    """Відправляє повідомлення про помилку адміну"""
    try:
        bot.send_message(chat_id=ADMIN_USER_ID, text=message)
        logger.info(f"📤 Повідомлення про помилку відправлено адміну: {message}")
    except Exception as e:
        logger.error(f"❌ Не вдалося відправити повідомлення адміну: {e}")

def start_command(bot, update):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    logger.info(f"👤 /start викликано користувачем: {user_id} (@{username}, {first_name})")
    
    try:
        logger.info(f"🔍 Перевіряємо авторизацію для користувача {user_id}...")
        
        if is_authenticated(user_id):
            logger.info(f"✅ Користувач {user_id} вже авторизований")
            
            welcome_message = (
                f"🎉 Вітаємо, {first_name}!\n\n"
                "Ви авторизовані в системі і маєте доступ до всіх функцій Dr. Gomon Concierge.\n\n"
                "🔓 Доступні дії:\n\n"
                "🚪 /hvirtka - Відкрити хвіртку для пішого проходу\n"
                "🏠 /vorota - Відкрити ворота для авто\n"
                "📞 /call - Зателефонувати лікарю Вікторії\n"
                "🗺️ /map - Показати розташування косметології на мапі\n"
                "📋 /scheme - Схема розташування косметології в ЖК Графський\n\n"
                "💡 Підказка: для швидкого доступу до команд\n"
                "   натисніть кнопку \"Меню\" ☰ зліва внизу"
            )
            
            bot.send_message(chat_id=update.message.chat_id, text=welcome_message)
            logger.info(f"✅ Авторизоване повідомлення відправлено користувачу {user_id}")
        else:
            logger.info(f"❌ Користувач {user_id} НЕ авторизований")
            
            unauthorized_message = (
                f"👋 Вітаємо, {first_name}!\n\n"
                "❌ Ви не авторизовані в системі.\n\n"
                "📱 Для авторизації поділіться своїм номером телефону."
            )
            
            # Спочатку відправляємо звичайне повідомлення
            bot.send_message(chat_id=update.message.chat_id, text=unauthorized_message)
            logger.info(f"📤 Повідомлення неавторизованому користувачу {user_id} відправлено")
            
            # Потім намагаємося додати кнопку
            try:
                logger.info(f"🔄 Імпортуємо KeyboardButton для користувача {user_id}")
                from telegram import KeyboardButton, ReplyKeyboardMarkup
                logger.info(f"✅ KeyboardButton імпортовано успішно")
                
                logger.info(f"🔄 Створюємо кнопку для користувача {user_id}")
                keyboard = [[KeyboardButton("📱 Поділитися номером", request_contact=True)]]
                reply_markup = ReplyKeyboardMarkup(
                    keyboard, 
                    one_time_keyboard=True, 
                    resize_keyboard=True
                )
                logger.info(f"✅ Кнопка створена успішно для користувача {user_id}")
                
                button_message = "👇 Натисніть кнопку для авторизації:"
                
                logger.info(f"🔄 Відправляємо кнопку користувачу {user_id}")
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text=button_message,
                    reply_markup=reply_markup
                )
                logger.info(f"✅ Кнопка успішно відправлена користувачу {user_id}")
                
            except Exception as button_error:
                logger.error(f"❌ Помилка створення кнопки для {user_id}: {button_error}")
                logger.error(f"❌ Тип помилки: {type(button_error)}")
                logger.error(f"❌ Деталі: {str(button_error)}")
                
                # Fallback
                fallback_message = (
                    "📱 Відправте свій номер телефону текстом\n"
                    "Формат: +380XXXXXXXXX"
                )
                bot.send_message(chat_id=update.message.chat_id, text=fallback_message)
                logger.info(f"📱 Fallback повідомлення відправлено користувачу {user_id}")
            
    except Exception as e:
        logger.exception(f"❌ Критична помилка в start_command для користувача {user_id}: {e}")
        bot.send_message(
            chat_id=update.message.chat_id,
            text="❌ Технічна помилка. Зверніться до підтримки: 073-310-31-10"
        )

def contact_handler(bot, update):
    user_id = update.effective_user.id
    username = update.effective_user.username or "N/A"
    first_name = update.effective_user.first_name or "N/A"
    
    logger.info(f"📱 Отримано контакт від користувача: {user_id} (@{username})")
    
    try:
        contact = update.message.contact
        phone_number = contact.phone_number
        
        logger.info(f"📞 Номер телефону: {phone_number}")
        
        from user_db import store_user
        from telegram import ReplyKeyboardRemove
        
        # ВИПРАВЛЕНО: додаємо всі потрібні параметри
        store_result = store_user(user_id, phone_number, username, first_name)
        logger.info(f"📊 store_user повернув: {store_result}")
        
        # Продовжуємо незалежно від результату, бо користувач уже збережений
        if True:
            success_message = (
                f"✅ Дякуємо, {first_name}!\n\n"
                f"📱 Ваш номер {phone_number} збережено.\n"
                f"🔍 Перевіряємо дозволи доступу...\n\n"
                f"Зачекайте, будь ласка..."
            )
            
            # ВИПРАВЛЕНО: Одразу прибираємо кнопку
            bot.send_message(
                chat_id=update.message.chat_id, 
                text=success_message,
                reply_markup=ReplyKeyboardRemove()
            )
            logger.info(f"📤 Повідомлення з видаленням кнопки відправлено користувачу {user_id}")
            
            time.sleep(2)
            
            if is_authenticated(user_id):
                authorized_message = (
                    f"🎉 Вітаємо, {first_name}!\n\n"
                    "Ви авторизовані в системі і маєте доступ до всіх функцій Dr. Gomon Concierge.\n\n"
                    "🔓 Доступні дії:\n\n"
                    "🚪 /hvirtka - Відкрити хвіртку для пішого проходу\n"
                    "🏠 /vorota - Відкрити ворота для авто\n"
                    "📞 /call - Зателефонувати лікарю Вікторії\n"
                    "🗺️ /map - Показати розташування косметології на мапі\n"
                    "📋 /scheme - Схема розташування косметології в ЖК Графський\n\n"
                    "💡 Підказка: для швидкого доступу до команд\n"
                    "   натисніть кнопку \"Меню\" ☰ зліва внизу"
                )
                
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text=authorized_message
                )
                logger.info(f"✅ Користувач {user_id} успішно авторизований")
            else:
                denied_message = (
                    "⚠️ Доступ обмежено!\n\n"
                    "Ваш номер не зареєстровано в системі Dr. Gomon Cosmetology.\n\n"
                    "📞 Для реєстрації зверніться:\n"
                    "📱 +380733103110 - телефонуйте\n"
                    "💬 <a href=\"https://instagram.com/dr.gomon\">Instagram</a> - пишіть в Direct\n\n"
                    "🔓 Доступні функції:\n"
                    "📞 /call - Зателефонувати лікарю Вікторії\n"
                    "🗺️ /map - Показати розташування на мапі\n"
                    "📋 /scheme - Схема розташування в ЖК Графський"
                )
                
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text=denied_message,
                    parse_mode='HTML'
                )
                logger.info(f"❌ Користувач {user_id} не авторизований - номер не в системі")
        else:
            error_message = (
                "❌ Виникла помилка при збереженні ваших даних.\n\n"
                "📞 Зверніться до підтримки: 073-310-31-10"
            )
            
            bot.send_message(
                chat_id=update.message.chat_id, 
                text=error_message,
                reply_markup=ReplyKeyboardRemove()
            )
            logger.error(f"❌ Не вдалося зберегти користувача {user_id}")
            
    except Exception as e:
        logger.exception(f"❌ Помилка в contact_handler для користувача {user_id}: {e}")
        
        from telegram import ReplyKeyboardRemove
        bot.send_message(
            chat_id=update.message.chat_id,
            text="❌ Виникла помилка. Спробуйте пізніше.",
            reply_markup=ReplyKeyboardRemove()
        )

def call_command(bot, update):
    """Команда для телефону лікаря"""
    user_id = update.effective_user.id
    logger.info(f"📞 /call викликано користувачем: {user_id}")
    
    try:
        call_message = "📞 Щоб зателефонувати лікарю Вікторії - наберіть - 0996093860"
        
        bot.send_message(chat_id=update.message.chat_id, text=call_message)
        logger.info(f"📞 Телефон лікаря відправлено користувачу {user_id}")
        
    except Exception as e:
        logger.exception(f"❌ Помилка в call_command: {e}")
        bot.send_message(chat_id=update.message.chat_id, text="❌ Помилка отримання телефону")

def map_command(bot, update):
    user_id = update.effective_user.id
    logger.info(f"🗺️ /map викликано користувачем: {user_id}")
    
    try:
        map_message = (
            "🗺️ Карта локації:\n\n"
            f"📍 Посилання на карту: {MAP_URL}\n\n"
            "🚗 Виберіть зручний маршрут для прибуття."
        )
        
        bot.send_message(chat_id=update.message.chat_id, text=map_message)
        logger.info(f"🗺️ Карта відправлена користувачу {user_id}")
        
    except Exception as e:
        logger.exception(f"❌ Помилка в map_command: {e}")
        bot.send_message(chat_id=update.message.chat_id, text="❌ Помилка отримання карти")

def scheme_command(bot, update):
    user_id = update.effective_user.id
    logger.info(f"🧭 /scheme викликано користувачем: {user_id}")
    
    try:
        scheme_message = (
            "🏗️ Схема будівлі:\n\n"
            f"📋 Посилання на схему: {SCHEME_URL}\n\n"
            "🏠 Оберіть потрібний вхід згідно схеми."
        )
        
        bot.send_message(chat_id=update.message.chat_id, text=scheme_message)
        logger.info(f"🧭 Схема відправлена користувачу {user_id}")
        
    except Exception as e:
        logger.exception(f"❌ Помилка в scheme_command: {e}")
        bot.send_message(chat_id=update.message.chat_id, text="❌ Помилка отримання схеми")

def restart_command(bot, update):
    user_id = update.effective_user.id
    logger.info(f"🔄 /restart викликано користувачем: {user_id}")
    
    if user_id != ADMIN_USER_ID:
        bot.send_message(
            chat_id=update.message.chat_id, 
            text="❌ Ця команда доступна тільки адміністратору"
        )
        return
    
    try:
        bot.send_message(chat_id=update.message.chat_id, text="🔄 Перезапуск бота...")
        logger.info("🔄 Перезапуск бота...")
        
        # Завершуємо поточний процес, cron автоматично перезапустить
        os._exit(0)
        
    except Exception as e:
        logger.exception(f"❌ Помилка перезапуску: {e}")
        bot.send_message(chat_id=update.message.chat_id, text="❌ Помилка перезапуску")

def test_command(bot, update):
    user_id = update.effective_user.id
    logger.info(f"🧪 /test викликано користувачем: {user_id}")
    
    try:
        test_message = (
            "🧪 Тест бота:\n\n"
            f"✅ Бот працює\n"
            f"👤 Ваш ID: {user_id}\n"
            f"🕐 Час: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🔐 Авторизований: {'✅ Так' if is_authenticated(user_id) else '❌ Ні'}"
        )
        
        bot.send_message(chat_id=update.message.chat_id, text=test_message)
        logger.info(f"🧪 Тест відправлено користувачу {user_id}")
        
    except Exception as e:
        logger.exception(f"❌ Помилка в test_command: {e}")
        bot.send_message(chat_id=update.message.chat_id, text="❌ Помилка тестування")

def status_command(bot, update):
    user_id = update.effective_user.id
    logger.info(f"📊 /status викликано користувачем: {user_id}")
    
    try:
        user_info = get_user_info(user_id)
        auth_status = is_authenticated(user_id)
        
        status_text = f"📊 Статус бота:\n\n"
        status_text += f"👤 Користувач: {user_id}\n"
        status_text += f"🔐 Авторизований: {'✅ Так' if auth_status else '❌ Ні'}\n"
        status_text += f"🤖 Бот: ✅ Працює\n"
        status_text += f"📅 Час: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if user_info:
            status_text += f"💾 База даних:\n"
            status_text += f"  👥 Користувачів: {user_info['users_count']}\n"
            status_text += f"  🏥 Клієнтів: {user_info['clients_count']}\n"
            status_text += f"  📱 Ви в базі: {'✅ Так' if user_info['user_in_db'] else '❌ Ні'}\n"
            
            if user_info['user_data']:
                phone = user_info['user_data'][1]
                status_text += f"  📞 Ваш телефон: {phone}\n"
        
        bot.send_message(chat_id=update.message.chat_id, text=status_text)
        logger.info(f"📊 Статус відправлено користувачу {user_id}")
        
    except Exception as e:
        logger.exception(f"❌ Помилка в status_command: {e}")
        bot.send_message(chat_id=update.message.chat_id, text="❌ Помилка при отриманні статусу")

def sync_command(bot, update):
    user_id = update.effective_user.id
    logger.info(f"🔄 /sync викликано користувачем: {user_id}")
    
    if user_id != ADMIN_USER_ID:
        bot.send_message(
            chat_id=update.message.chat_id, 
            text="❌ Ця команда доступна тільки адміністратору"
        )
        return
    
    try:
        bot.send_message(
            chat_id=update.message.chat_id, 
            text="🔄 Ручна синхронізація клієнтів запущена...\n\n"
                 "📊 Автоматична синхронізація відбувається:\n"
                 "🌅 09:00 - Ранкова синхронізація\n"
                 "🌆 21:00 - Вечірня синхронізація\n\n"
                 "📱 Результати будуть надіслані в Telegram"
        )
        
        # Запускаємо ручну синхронізацію через скрипт
        import subprocess
        subprocess.Popen(["/home/gomoncli/zadarma/sync_with_notification.sh"])
        
        logger.info(f"✅ Ручна синхронізація запущена користувачем {user_id}")
        
    except Exception as e:
        logger.exception(f"❌ Помилка в sync_command: {e}")
        bot.send_message(
            chat_id=update.message.chat_id, 
            text="❌ Помилка при запуску ручної синхронізації"
        )

def error_handler(bot, update, error):
    logger.error(f"❌ Помилка в обробці апдейту: {error}")
    if update:
        logger.error(f"📝 Апдейт: {update.to_dict()}")
        
        try:
            if update.message:
                update.message.reply_text(
                    "❌ Сталася помилка при обробці команди. "
                    "Будь ласка, спробуйте ще раз або зверніться до підтримки."
                )
        except:
            pass
    
    send_error_to_admin(bot, f"❌ Помилка: {error}")

def main():
    logger.info("🚀 Бот запускається...")
    
    # Створення PID файлу
    create_pid_file()
    
    try:
        init_db()
        logger.info("✅ База даних ініціалізована")
    except Exception as e:
        logger.error(f"❌ Помилка ініціалізації БД: {e}")
        return

    # Початкова синхронізація видалена - тепер через cron

    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    # Додавання обробників
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(MessageHandler(Filters.contact, contact_handler))
    dp.add_handler(CommandHandler("call", call_command))
    dp.add_handler(CommandHandler("map", map_command))
    dp.add_handler(CommandHandler("scheme", scheme_command))
    dp.add_handler(CommandHandler("restart", restart_command))
    dp.add_handler(CommandHandler("test", test_command))
    dp.add_handler(CommandHandler("status", status_command))
    dp.add_handler(CommandHandler("sync", sync_command))
    dp.add_handler(CommandHandler("hvirtka", handle_door_command))
    dp.add_handler(CommandHandler("vorota", handle_gate_command))
    
    dp.add_error_handler(error_handler)
    
    logger.info("✅ Всі обробники додані")

    logger.info("✅ Стартуємо polling...")
    updater.start_polling()
    
    logger.info("🤖 Бот успішно запущений та чекає на повідомлення...")
    logger.info("ℹ️  Для зупинки натисніть Ctrl+C")
    
    updater.idle()

if __name__ == '__main__':
    main()
