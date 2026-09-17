import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Web server for Render Free Tier
app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# Bot logic
ADMIN_USER_ID = 6282253982
TELEGRAM_BOT_TOKEN = "YOUR_NEW_TELEGRAM_BOT_TOKEN"
HERO_API_KEY = "YOUR_NEW_HERO_SMS_API_KEY"
HERO_BASE_URL = "https://hero-sms.com/stubs/handler_api.php"

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_USER_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ দুঃখিত! আপনার এই বট ব্যবহার করার অনুমতি নেই।")
        return
    await update.message.reply_text(
        "স্বাগতম অ্যাডমিন! 👋\n\n"
        "উপলব্ধ কমান্ডসমূহ:\n"
        "/balance - HeroSMS ব্যালেন্স দেখতে\n"
        "/getnum - টেলিগ্রামের জন্য নম্বর কিনতে"
    )

async def get_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    response = requests.get(HERO_BASE_URL, params={"api_key": HERO_API_KEY, "action": "getBalance"})
    if "ACCESS_BALANCE" in response.text:
        balance = response.text.split(":")[1]
        await update.message.reply_text(f"💳 আপনার বর্তমান ব্যালেন্স: ${balance}")
    else:
        await update.message.reply_text(f"❌ সমস্যা হয়েছে: {response.text}")

async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    response = requests.get(HERO_BASE_URL, params={
        "api_key": HERO_API_KEY,
        "action": "getNumber",
        "service": "tg",
        "country": 0
    })
    if "ACCESS_NUMBER" in response.text:
        data = response.text.split(":")
        await update.message.reply_text(f"📱 **নতুন নম্বর:** `{data[2]}`\n**আইডি:** `{data[1]}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ নম্বর পাওয়া যায়নি: {response.text}")

if __name__ == '__main__':
    Thread(target=run_web).start()
    bot = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("balance", get_balance))
    bot.add_handler(CommandHandler("getnum", get_number))
    bot.run_polling()
