import json
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
import requests

LLAMA_API_URL = "http://localhost:11434/api/generate"
API_TOKEN = "Token"  # get it from @BotFather
ALLOWED_IDS = [000, 111]  # allowed user ids

model_map = {
    "1": "llama3",
    "2": "mistral",
    "3": "gemma",
    "4": "mixtral",
    "5": "dolphin-mixtral",
    "6": "dolphin-llama3",
}

conn = sqlite3.connect("user_models.db")
c = conn.cursor()

c.execute(
    """CREATE TABLE IF NOT EXISTS user_models
                     (user_id INTEGER PRIMARY KEY, default_model TEXT)"""
)
conn.commit()

CHOOSING, SETTING = range(2)


def get_default_model(user_id):
    c.execute("SELECT default_model FROM user_models WHERE user_id=?", (user_id,))
    result = c.fetchone()
    return result[0] if result else "llama3"


async def generate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    model = get_default_model(update.effective_user.id)
    print(update)
    prompt = update.message.text.replace("/promt", "").strip()
    if not prompt:
        await update.message.reply_text("Пожалуйста, введите запрос после /promt")
        return

    payload = {"model": model, "prompt": prompt}
    response = requests.post(LLAMA_API_URL, json=payload, stream=True)
    full_response = ""
    for line in response.iter_lines():
        if line:
            response_json = json.loads(line)
            if response_json["done"]:
                full_response += response_json["response"]
                await update.message.reply_text(full_response)
                break
            else:
                full_response += response_json["response"]


async def unauthorized_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Доступ запрещен. У вас нет разрешения на использование этого бота."
    )


async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [
            InlineKeyboardButton("Meta Llama 3 - 8B", callback_data="1"),
            InlineKeyboardButton("Mistral - 7B", callback_data="2"),
        ],
        [
            InlineKeyboardButton("Gemma - 9B", callback_data="3"),
            InlineKeyboardButton("Mixtral - 8x7B", callback_data="4"),
        ],
        [
            InlineKeyboardButton("Dolphin-Mixtral - 8x7B", callback_data="5"),
            InlineKeyboardButton("Dolphin-Llama3 - 8B", callback_data="6"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите новую модель:", reply_markup=reply_markup)
    return CHOOSING


async def choose_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_choice = query.data
    user_id = query.from_user.id
    model = model_map.get(user_choice)

    if not model:
        await query.answer("Неверный выбор. Пожалуйста, выберите снова.")
        return CHOOSING

    c.execute(
        "INSERT OR REPLACE INTO user_models (user_id, default_model) VALUES (?, ?)",
        (user_id, model),
    )
    conn.commit()

    await query.edit_message_text(f"Модель по умолчанию установлена: {model}")

    return ConversationHandler.END


app = ApplicationBuilder().token(API_TOKEN).build()


app.add_handler(
    CommandHandler("setmodel", set_model, filters=filters.User(user_id=ALLOWED_IDS))
)


app.add_handler(CallbackQueryHandler(choose_model, pattern=r"^[1-6]$"))
app.add_handler(
    MessageHandler(
        filters=filters.ALL
        & filters.ChatType.PRIVATE
        & filters.User(user_id=ALLOWED_IDS),
        callback=generate_text,
    )
)
app.add_handler(
    CommandHandler("promt", generate_text, filters=filters.User(user_id=ALLOWED_IDS))
)
app.add_handler(
    MessageHandler(
        filters=~filters.User(user_id=ALLOWED_IDS),
        callback=unauthorized_user,
    )
)
app.run_polling()
