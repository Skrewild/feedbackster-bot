import logging
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime
import os
import csv

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# CSV File name
LOG_FILE = "feedback_log.csv"

# Ensure CSV file exists with header
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["User ID", "Username", "Timestamp", "Feedback"])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправьте мне ваше сообщение, и я передам его администратору.")

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    feedback = update.message.text
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Save to CSV
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([user.id, user.username or "None", timestamp, feedback])

    # Notify admin
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Новое сообщение от @{user.username or user.id}:\n{feedback}")

    # Confirm receipt to sender
    await update.message.reply_text("Спасибо за ваше сообщение!")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback))

    app.run_polling()
