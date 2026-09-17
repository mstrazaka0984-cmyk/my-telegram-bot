import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# অ্যাডমিন লক আইডি
ADMIN_USER_ID = 6282253982

# আপনার প্রদান করা সিক্রেট ক্রেডেনশিয়ালস
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
    response = requests.get(HERO_BASE_URL, params={
        "api_key": HERO_API_KEY,
        "action": "getBalance"
    })
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
        activation_id = data[1]
        phone_number = data[2]
        msg = (
            f"📱 **নতুন নম্বর পাওয়া গেছে!**\n\n"
            f"**নম্বর:** `{phone_number}`\n"
            f"**অ্যাক্টিভেশন আইডি:** `{activation_id}`"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ নম্বর পাওয়া যায়নি: {response.text}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", get_balance))
    app.add_handler(CommandHandler("getnum", get_number))
    print("বট সফলভাবে চালু হয়েছে...")
    app.run_polling()
