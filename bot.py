import logging
import os
import sys
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from zadarma_api import make_callback  # Маємо функцію дзвінка через Zadarma API
from config import ZADARMA_FROM, NUM_HVIRTKA, NUM_VOROTA  # Номери та налаштування

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def hvirtka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/hvirtka command from user {update.effective_user.id}")
    response = await make_callback(ZADARMA_FROM, NUM_HVIRTKA)
    await update.message.reply_text(f"Ініціюю дзвінок на хвіртку ({NUM_HVIRTKA}).\nРезультат: {response}")

async def vorota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/vorota command from user {update.effective_user.id}")
    response = await make_callback(ZADARMA_FROM, NUM_VOROTA)
    await update.message.reply_text(f"Ініціюю дзвінок на ворота ({NUM_VOROTA}).\nРезультат: {response}")

async def map_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/map command from user {update.effective_user.id}")
    url = "https://maps.google.com/?q=Kyiv"  # Тут твій хардкод лінк на карту
    await update.message.reply_text(f"Ось карта: {url}")

async def scheme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/scheme command from user {update.effective_user.id}")
    # Хардкод лінку на зображення Google Drive
    url = "https://drive.google.com/uc?id=YOUR_IMAGE_ID"
    await update.message.reply_text(f"Ось схема: {url}")

async def call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/call command from user {update.effective_user.id}")
    direct_number = "0996093860"
    await update.message.reply_text(f"Зателефонуйте напряму за номером: {direct_number}")

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/restart command from user {update.effective_user.id}")
    await update.message.reply_text("Перезапускаю бота...")
    # Перезапуск скрипта
    os.execv(sys.executable, [sys.executable] + sys.argv)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Unknown command from user {update.effective_user.id}: {update.message.text}")
    await update.message.reply_text("Невідома команда. Спробуйте /hvirtka, /vorota, /map, /scheme, /call або /restart.")

def main():
    from telegram.ext import MessageHandler, filters

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
        return

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("hvirtka", hvirtka))
    app.add_handler(CommandHandler("vorota", vorota))
    app.add_handler(CommandHandler("map", map_cmd))
    app.add_handler(CommandHandler("scheme", scheme))
    app.add_handler(CommandHandler("call", call))
    app.add_handler(CommandHandler("restart", restart))

    # Обробник невідомих команд
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    logger.info("Starting bot polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
