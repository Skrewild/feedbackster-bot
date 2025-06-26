import os
import logging
import csv
from datetime import datetime
import requests

from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}

LOG_FILE = "feedback_log.csv"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет, {user.mention_html()}! 👋\n"
        "Отправьте ваше мнение или отзыв, и я сохраню его.",
        reply_markup=ForceReply(selective=True),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ Просто напишите сообщение, и я сохраню его как отзыв.\n"
        "Администратор может использовать /summary для анализа отзывов."
    )

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    feedback = update.message.text

    is_new_file = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, mode="a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        if is_new_file:
            writer.writerow(["date", "user_id", "username", "feedback"])
        writer.writerow(
            [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                user.id,
                user.username or "unknown",
                feedback.replace("\n", " "),
            ]
        )

    await update.message.reply_text("✅ Спасибо за ваш отзыв!")

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
        combined_feedback = "\n".join(feedbacks[:50])  # limit to 50 for brevity

    prompt = (
        "Summarize the following customer feedback into key themes, complaints, suggestions, "
        "and overall sentiment:\n\n" + combined_feedback
    )

    try:
        response = requests.post(
            HF_API_URL,
            headers=HEADERS,
            json={"inputs": prompt}
        )
        result = response.json()

        if isinstance(result, list) and 'generated_text' in result[0]:
            summary_text = result[0]['generated_text'].strip()
        elif 'error' in result:
            summary_text = f"Ошибка Hugging Face API: {result['error']}"
        else:
            summary_text = "⚠️ Не удалось получить ответ от модели."

        await update.message.reply_text(f"📝 Резюме:\n{summary_text}")

    except Exception as e:
        logging.error(f"Hugging Face API error: {e}")
        await update.message.reply_text("❌ Ошибка при обращении к Hugging Face API.")

def main() -> None:
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback))

    app.run_polling()

if __name__ == "__main__":
    main()
