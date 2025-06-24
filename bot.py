from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import os
from datetime import datetime

ADMIN_ID = 1710485408
TOKEN = "7971843772:AAFX_pKL9OAWBnGqsgEiDOPB3ITSgZlAiic"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Приветствую! Я Фидбекстер, бот для сбора обратной связи. ✉️\n"
        "Отправьте свои мысли с помощью команды:\n"
        "/feedback ваш отзыв"
    )

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    feedback_text = ' '.join(context.args)

    if not feedback_text:
        await update.message.reply_text(
            "Пожалуйста, напишите отзыв после команды. /feedback \n"
            "Пример: /feedback Бот очень классный!"
        )
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {user.full_name} (Телеграм: @{user.username})\n{feedback_text}\n\n"

    with open("feedback_log.txt", "a", encoding="utf-8") as file:
        file.write(entry)

    await update.message.reply_text("✅ Спасибо! Ваш отзыв сохранен.")

async def view_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 У тебя нет прав для этой команды.")
        return

    try:
        with open("feedback_log.txt", "r", encoding="utf-8") as file:
            content = file.read()

        if not content.strip():
            await update.message.reply_text("Файл с отзывами пуст.")
        else:
            chunks = [content[i:i+4000] for i in range(0, len(content), 4000)]
            for chunk in chunks:
                await update.message.reply_text(f"📄 Отзывы:\n\n{chunk}")
    except FileNotFoundError:
        await update.message.reply_text("Файл с отзывами не найден.")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("feedback", feedback))
    app.add_handler(CommandHandler("view_feedback", view_feedback))


    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
