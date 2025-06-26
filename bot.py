import os
import logging
import csv
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

# Load environment variables
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Log file path
LOG_FILE = "feedback_log.csv"

# Logging config
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет, {user.mention_html()}! 👋\nОтправьте ваше мнение или отзыв, и я сохраню его.",
        reply_markup=ForceReply(selective=True),
    )

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ Просто напишите сообщение, и я сохраню его как отзыв.\nАдминистратор может использовать /summary для анализа отзывов."
    )

# Feedback handler
async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    feedback = update.message.text

    is_new_file = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, mode="a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        if is_new_file:
            writer.writerow(["date", "user_id", "username", "feedback"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user.id,
            user.username or "unknown",
            feedback.replace("\n", " "),
        ])

    await update.message.reply_text("✅ Спасибо за ваш отзыв!")

# Summary command (admin only)
async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Эта команда доступна только администратору.")
        return

    if not os.path.exists(LOG_FILE):
        await update.message.reply_text("Файл с отзывами не найден.")
        return

    with open(LOG_FILE, encoding="utf-8") as f:
        lines = f.readlines()[1:]
        if not lines:
            await update.message.reply_text("Пока нет отзывов для анализа.")
            return
        feedbacks = [line.strip().split(",")[3] for line in lines if len(line.strip().split(",")) >= 4]
        combined_feedback = "\n".join(feedbacks[:50])

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that summarizes customer feedback for business improvement."
                },
                {
                    "role": "user",
                    "content": f"Summarize the following feedback into key themes, complaints, suggestions, and overall sentiment:\n\n{combined_feedback}"
                }
            ],
            max_tokens=500
        )
        summary_text = response.choices[0].message.content.strip()
        await update.message.reply_text(f"📝 Резюме:\n{summary_text}")
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        await update.message.reply_text("❌ Ошибка при обращении к OpenAI API.")

# Main function
def main() -> None:
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("summary", summary))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback))

    logging.info("Бот запущен и ожидает сообщения...")
    app.run_polling()

if __name__ == "__main__":
    main()
