import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

ADMIN_USER_ID = 6282253982
TELEGRAM_BOT_TOKEN = "8789966847:AAH0RMLgxUyEFsmgwcujFHrtvX6eel7yecg"
HERO_API_KEY = "d038528eA9dAf95998A99c70de23e695"
HERO_BASE_URL = "https://hero-sms.com/stubs/handler_api.php"

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_USER_ID

def get_reply_keyboard():
    keyboard = [
        [KeyboardButton("💳 Balance"), KeyboardButton("📱 Get Number")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ দুঃখিত! আপনার এই বট ব্যবহার করার অনুমতি নেই।")
        return
    await update.message.reply_text(
        "স্বাগতম অ্যাডমিন! 👋\n\nনিচের কিবোর্ড বাটনগুলো ব্যবহার করে কমান্ড দিন:",
        reply_markup=get_reply_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    text = update.message.text

    if text in ["💳 Balance", "/balance"]:
        response = requests.get(HERO_BASE_URL, params={"api_key": HERO_API_KEY, "action": "getBalance"})
        if "ACCESS_BALANCE" in response.text:
            balance = response.text.split(":")[1]
            await update.message.reply_text(f"💳 আপনার বর্তমান ব্যালেন্স: ${balance}", reply_markup=get_reply_keyboard())
        else:
            await update.message.reply_text(f"❌ সমস্যা হয়েছে: {response.text}", reply_markup=get_reply_keyboard())

    elif text in ["📱 Get Number", "/getnum"]:
        response = requests.get(HERO_BASE_URL, params={
            "api_key": HERO_API_KEY,
            "action": "getNumber",
            "service": "tg",
            "country": 0
        })
        if "ACCESS_NUMBER" in response.text:
            data = response.text.split(":")
            await update.message.reply_text(f"📱 **নতুন নম্বর:** `{data[2]}`\n**আইডি:** `{data[1]}`", parse_mode="Markdown", reply_markup=get_reply_keyboard())
        else:
            await update.message.reply_text(f"❌ নম্বর পাওয়া যায়নি: {response.text}", reply_markup=get_reply_keyboard())

if __name__ == '__main__':
    Thread(target=run_web).start()
    bot = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("balance", handle_message))
    bot.add_handler(CommandHandler("getnum", handle_message))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
