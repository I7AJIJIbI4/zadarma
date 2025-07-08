import logging
from telegram.ext import Updater, CommandHandler
from config import TELEGRAM_TOKEN, ZADARMA_API_KEY, ZADARMA_API_SECRET, ZADARMA_FROM_NUMBER, HVIRTKA_NUMBER, VOROTA_NUMBER
from zadarma_api import make_zadarma_call

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update, context):
    update.message.reply_text(
        "Привіт! Використовуй команди:\n"
        "/hvirtka - відчинити хвіртку\n"
        "/vorota - відчинити ворота\n"
        "/map - показати карту\n"
        "/scheme - показати схему\n"
        "/call - дзвінок напряму"
    )

def hvirtka(update, context):
    update.message.reply_text("Відчиняю хвіртку...")
    result = make_zadarma_call(ZADARMA_FROM_NUMBER, HVIRTKA_NUMBER)
    update.message.reply_text(f"Результат дзвінка: {result}")

def vorota(update, context):
    update.message.reply_text("Відчиняю ворота...")
    result = make_zadarma_call(ZADARMA_FROM_NUMBER, VOROTA_NUMBER)
    update.message.reply_text(f"Результат дзвінка: {result}")

def map_cmd(update, context):
    url = "https://goo.gl/maps/your_hardcoded_link"
    update.message.reply_text(f"Ось карта: {url}")

def scheme(update, context):
    img_link = "https://drive.google.com/your_hardcoded_image_link"
    update.message.reply_text(f"Ось схема: {img_link}")

def call(update, context):
    update.message.reply_text("Щоб зателефонувати, набери: 0996093860")

def error(update, context):
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("hvirtka", hvirtka))
    dp.add_handler(CommandHandler("vorota", vorota))
    dp.add_handler(CommandHandler("map", map_cmd))
    dp.add_handler(CommandHandler("scheme", scheme))
    dp.add_handler(CommandHandler("call", call))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
