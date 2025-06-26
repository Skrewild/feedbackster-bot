import logging
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime
import os
import csv
from textblob import TextBlob  

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

LOG_FILE = "feedback_log.csv"


if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["User ID", "Username", "Timestamp", "Feedback", "Sentiment", "Polarity"])


def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        label = "Положительное"
    elif polarity < -0.1:
        label = "Отрицательное"
    else:
        label = "Нейтральное"
    return label, round(polarity, 2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправьте мне ваше сообщение, и я передам его администратору.")


async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    feedback = update.message.text
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    sentiment_label, polarity = analyze_sentiment(feedback)

    
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([user.id, user.username or "None", timestamp, feedback, sentiment_label, polarity])

    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"Новое сообщение от @{user.username or user.id}:\n"
            f"✉️ {feedback}\n"
            f"📊 Настроение: {sentiment_label} ({polarity:+})"
        )
    )

    
    await update.message.reply_text("Спасибо за ваше сообщение!")


async def get_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Извините, эта команда доступна только администратору.")
        return

    if os.path.exists(LOG_FILE):
        await context.bot.send_document(chat_id=update.message.chat_id, document=open(LOG_FILE, "rb"))
    else:
        await update.message.reply_text("Файл с логами не найден.")


if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("getlog", get_log))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback))

    app.run_polling()
