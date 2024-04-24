import json
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

LLAMA_API_URL = "http://localhost:11434/api/generate"
API_TOKEN = "Token here"  # get it from @BotFather
ALLOWED_IDS = [0000, 0000]  # allowed user ids

logging.basicConfig(
    filename="update_log.txt",
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


async def generate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(update)
    # Uncomment the following lines if you want to restrict access to specific users
    # id = update.effective_user.id
    # if id not in ALLOWED_IDS:
    #   await update.message.reply_text(
    #        "Access denied. You do not have permission to use this bot."
    #   )
    #   return
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
                await update.message.reply_text(full_response)
                break
            else:
                full_response += response_json["response"]


app = ApplicationBuilder().token(API_TOKEN).build()
app.add_handler(CommandHandler("promt", generate_text))
app.run_polling()
