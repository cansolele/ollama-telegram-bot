import json
import sqlite3
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
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
import re
import base64

LLAMA_API_URL = "http://localhost:11434/api/generate"
API_TOKEN = "TOKEN"
ALLOWED_IDS = [000, 000]


model_button = KeyboardButton("⚙️ Сменить модель")
help_button = KeyboardButton("❓ Помощь")
keyboard = [[model_button, help_button]]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

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


def md_autofixer(text: str) -> str:
    escape_chars = r"_*[]()~>#+-=|{}.!"
    return "".join("\\" + char if char in escape_chars else char for char in text)


async def generate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    model = get_default_model(update.effective_user.id)
    print(update)

    if update.message.text == "⚙️ Сменить модель":
        await set_model(update, context)
        return
    elif update.message.text == "❓ Помощь":
        await update.message.reply_text("Тут будет какая-нибудь справка")
        return

    if update.message.photo:

        photo = update.message.photo[-1]

        photo_file = await photo.get_file()

        photo_data = await photo_file.download_as_bytearray()

        base64_encoded_image = base64.b64encode(photo_data).decode("utf-8")

        payload = {
            "model": "llava:34b",
            "prompt": "What is in this picture?",
            "images": [base64_encoded_image],
        }

    elif update.message.video or update.message.animation:
        await update.message.reply_text(
            "Извините, обработка видео и GIF пока не поддерживается."
        )
        return

    else:
        if update.message.sticker:
            prompt = update.message.sticker.emoji
        else:
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
                await update.message.reply_text(
                    md_autofixer(full_response),
                    reply_markup=reply_markup,
                    parse_mode="MarkdownV2",
                )
                break
            else:
                full_response += response_json["response"]


async def unauthorized_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Доступ запрещен. У вас нет разрешения на использование этого бота."
    )


async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_model = get_default_model(update.effective_user.id)

    keyboard = [
        [
            InlineKeyboardButton(
                f"Meta Llama 3 - 8B {'✅' if current_model == 'llama3' else ''}",
                callback_data="1",
            ),
            InlineKeyboardButton(
                f"Mistral - 7B {'✅' if current_model == 'mistral' else ''}",
                callback_data="2",
            ),
        ],
        [
            InlineKeyboardButton(
                f"Gemma - 9B {'✅' if current_model == 'gemma' else ''}",
                callback_data="3",
            ),
            InlineKeyboardButton(
                f"Mixtral - 8x7B {'✅' if current_model == 'mixtral' else ''}",
                callback_data="4",
            ),
        ],
        [
            InlineKeyboardButton(
                f"Dolphin-Mixtral - 8x7B {'✅' if current_model == 'dolphin-mixtral' else ''}",
                callback_data="5",
            ),
            InlineKeyboardButton(
                f"Dolphin-Llama3 - 8B {'✅' if current_model == 'dolphin-llama3' else ''}",
                callback_data="6",
            ),
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
