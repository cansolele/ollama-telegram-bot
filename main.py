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
    Application,
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
import logging
from config import Config
from database import db

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

model_button = KeyboardButton("⚙️ Сменить модель")
help_button = KeyboardButton("❓ Помощь")
reset_button = KeyboardButton("🔄 Сбросить контекст")
keyboard = [[model_button, help_button], [reset_button]]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

CHOOSING, SETTING = range(2)


def md_autofixer(text: str) -> str:
    escape_chars = r"_*[]()~>#+-=|{}.!"
    return "".join("\\" + char if char in escape_chars else char for char in text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Привет! Я готов помочь вам. Используйте /help для получения справки.",
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(Config.MESSAGES["help"], reply_markup=reply_markup)


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset chat history"""
    user_id = update.effective_user.id
    db.reset_chat_history(user_id)
    await update.message.reply_text(
        Config.MESSAGES["context_reset"], reply_markup=reply_markup
    )


async def generate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    model = db.get_user_model(user_id)

    if update.message.text == "⚙️ Сменить модель":
        await set_model(update, context)
        return
    elif update.message.text == "❓ Помощь":
        await help_command(update, context)
        return
    elif update.message.text == "🔄 Сбросить контекст":
        await reset_command(update, context)
        return

    if update.message.photo:
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        photo_data = await photo_file.download_as_bytearray()
        base64_encoded_image = base64.b64encode(photo_data).decode("utf-8")

        # Для изображений используем модель llava напрямую через generate API
        payload = {
            "model": "llava:34b",
            "prompt": update.message.caption or "What is in this picture?",
            "images": [base64_encoded_image],
            "stream": True,
        }

        response = requests.post(Config.OLLAMA_API_URL, json=payload, stream=True)
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
        return

    elif update.message.video or update.message.animation:
        await update.message.reply_text(
            "Извините, обработка видео и GIF пока не поддерживается."
        )
        return

    # Получаем историю чата
    chat_history = db.get_chat_history(user_id)

    # Добавляем текущее сообщение
    user_message = (
        update.message.sticker.emoji if update.message.sticker else update.message.text
    )
    messages = chat_history + [{"role": "user", "content": user_message}]

    # Сохраняем сообщение пользователя
    db.add_to_history(user_id, "user", user_message)

    # Отправляем запрос с контекстом
    payload = {"model": model, "messages": messages, "stream": True}

    response = requests.post(Config.OLLAMA_CHAT_URL, json=payload, stream=True)
    full_response = ""

    for line in response.iter_lines():
        if line:
            response_json = json.loads(line)
            if response_json.get("done", False):
                break
            if "message" in response_json and "content" in response_json["message"]:
                full_response += response_json["message"]["content"]

    # Сохраняем ответ ассистента
    if full_response:
        db.add_to_history(user_id, "assistant", full_response)
        await update.message.reply_text(
            md_autofixer(full_response),
            reply_markup=reply_markup,
            parse_mode="MarkdownV2",
        )


async def unauthorized_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(Config.MESSAGES["unauthorized"])


async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    current_model = db.get_user_model(user_id)

    keyboard = []
    row = []
    for idx, (key, model) in enumerate(Config.MODELS.items(), 1):
        button = InlineKeyboardButton(
            f"{model['display_name']} {'✅' if current_model == model['name'] else ''}",
            callback_data=key,
        )
        row.append(button)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите модель:", reply_markup=reply_markup)
    return CHOOSING


async def choose_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user_choice = query.data
    user_id = query.from_user.id

    if user_choice not in Config.MODELS:
        await query.edit_message_text("Неверный выбор. Пожалуйста, выберите снова.")
        return CHOOSING

    model = Config.MODELS[user_choice]["name"]
    db.set_user_model(user_id, model)

    await query.edit_message_text(
        f"Модель по умолчанию установлена: {Config.MODELS[user_choice]['display_name']}"
    )
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token(Config.API_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^⚙️ Сменить модель$")
                & filters.User(user_id=Config.ALLOWED_IDS),
                set_model,
            )
        ],
        states={
            CHOOSING: [CallbackQueryHandler(choose_model, pattern=r"^[1-3]$")],
        },
        fallbacks=[],
        per_message=False,
    )

    application.add_handler(
        CommandHandler("start", start, filters.User(user_id=Config.ALLOWED_IDS))
    )
    application.add_handler(
        CommandHandler("help", help_command, filters.User(user_id=Config.ALLOWED_IDS))
    )
    application.add_handler(
        CommandHandler("reset", reset_command, filters.User(user_id=Config.ALLOWED_IDS))
    )
    application.add_handler(conv_handler)

    application.add_handler(
        MessageHandler(
            filters.ALL
            & filters.ChatType.PRIVATE
            & filters.User(user_id=Config.ALLOWED_IDS),
            generate_text,
        )
    )

    application.add_handler(
        MessageHandler(~filters.User(user_id=Config.ALLOWED_IDS), unauthorized_user)
    )

    application.run_polling()


if __name__ == "__main__":
    main()
