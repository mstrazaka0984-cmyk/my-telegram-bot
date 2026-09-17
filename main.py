import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# ২ টি Authorized User/Admin ID
ALLOWED_USERS = [6282253982, 8600579923]

TELEGRAM_BOT_TOKEN = "8789966847:AAH0RMLgxUyEFsmgwcujFHrtvX6eel7yecg"
HERO_API_KEY = "d038528eA9dAf95998A99c70de23e695"
HERO_BASE_URL = "https://hero-sms.com/stubs/handler_api.php"

def is_authorized(user_id: int) -> bool:
    return user_id in ALLOWED_USERS

# Permanent Main Menu
def get_reply_keyboard():
    keyboard = [
        [KeyboardButton("📱 Get Number"), KeyboardButton("💳 Balance")],
        [KeyboardButton("⚙️ Admin Panel")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ দুঃখিত! আপনার এই বট ব্যবহার করার অনুমতি নেই।")
        return
    await update.message.reply_text(
        "স্বাগতম! 👋\n\nনিচের MENU কিবোর্ড বাটনগুলো ব্যবহার করে কাজ করতে পারেন:",
        reply_markup=get_reply_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    text = update.message.text

    # Balance Command
    if text in ["💳 Balance", "/balance"]:
        response = requests.get(HERO_BASE_URL, params={"api_key": HERO_API_KEY, "action": "getBalance"})
        if "ACCESS_BALANCE" in response.text:
            balance = response.text.split(":")[1]
            await update.message.reply_text(f"💳 আপনার বর্তমান ব্যালেন্স: ${balance}", reply_markup=get_reply_keyboard())
        else:
            await update.message.reply_text(f"❌ সমস্যা হয়েছে: {response.text}", reply_markup=get_reply_keyboard())

    # Get Number Command (Egypt & Indonesia)
    elif text in ["📱 Get Number", "/getnum"]:
        inline_keyboard = [
            [InlineKeyboardButton("🇪🇬 Egypt (Telegram Low Rate)", callback_data="country_4")],
            [InlineKeyboardButton("🇮🇩 Indonesia (Telegram Low Rate)", callback_data="country_6")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await update.message.reply_text("দেশ সিলেক্ট করুন (Telegram Low Rate):", reply_markup=reply_markup)

    # Admin Panel Button
    elif text == "⚙️ Admin Panel":
        admin_keyboard = [
            [InlineKeyboardButton("💳 Check API Balance", callback_data="admin_balance")],
            [InlineKeyboardButton("👥 Admin List", callback_data="admin_list")],
            [InlineKeyboardButton("🟢 System Status", callback_data="admin_status")]
        ]
        reply_markup = InlineKeyboardMarkup(admin_keyboard)
        await update.message.reply_text("⚙️ **অ্যাডমিন কন্ট্রোল প্যানেল:**", parse_mode="Markdown", reply_markup=reply_markup)

# Callback Query Handler for Inline Buttons (Country Selection & Admin Actions)
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_authorized(query.from_user.id):
        return

    data = query.data

    # Handling Country Selection
    if data.startswith("country_"):
        country_code = data.split("_")[1]
        response = requests.get(HERO_BASE_URL, params={
            "api_key": HERO_API_KEY,
            "action": "getNumber",
            "service": "tg",
            "country": country_code
        })

        if "ACCESS_NUMBER" in response.text:
            res_data = response.text.split(":")
            await query.message.reply_text(
                f"📱 **নতুন নম্বর:** `{res_data[2]}`\n**আইডি:** `{res_data[1]}`", 
                parse_mode="Markdown", 
                reply_markup=get_reply_keyboard()
            )
        else:
            await query.message.reply_text(f"❌ নম্বর পাওয়া যায়নি: {response.text}", reply_markup=get_reply_keyboard())

    # Handling Admin Panel Actions
    elif data == "admin_balance":
        response = requests.get(HERO_BASE_URL, params={"api_key": HERO_API_KEY, "action": "getBalance"})
        if "ACCESS_BALANCE" in response.text:
            balance = response.text.split(":")[1]
            await query.message.reply_text(f"⚙️ [Admin Info]\n💳 HeroSMS Balance: ${balance}")
        else:
            await query.message.reply_text(f"❌ API Error: {response.text}")

    elif data == "admin_list":
        admin_text = "👥 **অনুমোদিত অ্যাডমিন তালিকা:**\n" + "\n".join([f"• `{uid}`" for uid in ALLOWED_USERS])
        await query.message.reply_text(admin_text, parse_mode="Markdown")

    elif data == "admin_status":
        await query.message.reply_text("🟢 **বট সার্ভিস স্ট্যাটাস:** সক্রিয় ও রানিং (Web Server Active)")

if __name__ == '__main__':
    Thread(target=run_web).start()
    bot = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("balance", handle_message))
    bot.add_handler(CommandHandler("getnum", handle_message))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # Callback Query Handler for Inline Buttons
    bot.add_handler(CallbackQueryHandler(handle_callback_query))
    
    bot.run_polling()
