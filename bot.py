import logging
from telegram.ext import Updater, CommandHandler
from config import TELEGRAM_TOKEN, HVIRTKA_NUMBER, VOROTA_NUMBER
from zadarma_api import make_zadarma_call_handler, get_my_sip_info

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(bot, update):
    pass  # нічого не відповідаємо

def map_cmd(bot, update):
    url = "https://goo.gl/maps/your_hardcoded_link"
    bot.send_message(chat_id=update.effective_chat.id, text=f"Ось карта: {url}")

def scheme(bot, update):
    img_link = "https://drive.google.com/your_hardcoded_image_link"
    bot.send_message(chat_id=update.effective_chat.id, text=f"Ось схема: {img_link}")

def call(bot, update):
    bot.send_message(chat_id=update.effective_chat.id, text="Щоб зателефонувати, набери: 0996093860")

def number(bot, update):
    bot.send_message(chat_id=update.effective_chat.id, text="Отримую інформацію про віртуальний номер...\n")
    response = get_my_sip_info()
    bot.send_message(chat_id=update.effective_chat.id, text=f"Інформація про номер:\n{response}")

def error(bot, update, error):
    logger.warning(f'Update {update} caused error {error}')

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("hvirtka", make_zadarma_call_handler(HVIRTKA_NUMBER)))
    dp.add_handler(CommandHandler("vorota", make_zadarma_call_handler(VOROTA_NUMBER)))
    dp.add_handler(CommandHandler("map", map_cmd))
    dp.add_handler(CommandHandler("scheme", scheme))
    dp.add_handler(CommandHandler("call", call))
    dp.add_handler(CommandHandler("number", number))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
