import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import requests

LLAMA_API_URL = "http://localhost:11434/api/generate"
API_TOKEN = "Token"  # get it from @BotFather
ALLOWED_IDS = [000, 1234]  # allowed user ids


async def generate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # print(update)
    prompt = update.message.text.replace("/promt", "").strip()
    if not prompt:
        await update.message.reply_text("Please provide a prompt after /promt")
        return
    payload = {
        "model": "llama3",  # choose your model
        "prompt": prompt,
    }
    response = requests.post(LLAMA_API_URL, json=payload, stream=True)

    full_response = ""
    for line in response.iter_lines():
        if line:
            response_json = json.loads(line)
            if response_json["done"]:
                full_response += response_json["response"]
                await update.message.reply_text(full_response, parse_mode="Markdown")
                break
            else:
                full_response += response_json["response"]


async def unauthorized_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Access denied. You do not have permission to use this bot."
    )


app = ApplicationBuilder().token(API_TOKEN).build()

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
        # Uncomment line below to filter out unauthorized users
        # filters=~filters.User(user_id=ALLOWED_IDS), callback=unauthorized_user
    )
)
app.run_polling()
