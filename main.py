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

# ১. মাস্টার অ্যাডমিন তালিকা (যারা ইউজার ও ব্যালেন্স কন্ট্রোল করবে)
ADMINS = [6282253982, 8600579923]

# ২. অনুমোদিত ইউজার তালিকা ও ডাটাবেস (মেমোরিতে সংরক্ষিত)
# Format: {user_id: balance}
USERS = {
    6282253982: 100.0,  # অ্যাডমিনদের ডিফল্ট ব্যালেন্স
    8600579923: 100.0
}

TELEGRAM_BOT_TOKEN = "8789966847:AAH0RMLgxUyEFsmgwcujFHrtvX6eel7yecg"
HERO_API_KEY = "d038528eA9dAf95998A99c70de23e695"
HERO_BASE_URL = "https://hero-sms.com/stubs/handler_api.php"

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def is_user(user_id: int) -> bool:
    return user_id in USERS

def get_keyboard(user_id: int):
    # অ্যাডমিনদের জন্য Admin Panel বাটন থাকবে
    if is_admin(user_id):
        keyboard = [
            [KeyboardButton("📱 Get Number"), KeyboardButton("💳 Balance")],
            [KeyboardButton("⚙️ Admin Panel")]
        ]
    # সাধারণ ইউজারদের জন্য শুধু মূল ফিচার থাকবে
    else:
        keyboard = [
            [KeyboardButton("📱 Get Number"), KeyboardButton("💳 Balance")]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user(user_id):
        await update.message.reply_text(f"⛔ দুঃখিত! আপনার সার্ভিস ব্যবহারের অনুমতি নেই।\nআপনার Telegram ID: `{user_id}`", parse_mode="Markdown")
        return
    
    await update.message.reply_text(
        "স্বাগতম! 👋\nনিচের MENU থেকে আপনার প্রয়োজনীয় অপশন সিলেক্ট করুন:",
        reply_markup=get_keyboard(user_id)
    )

# --- ADMIN COMMANDS ---

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("⚠️ ফরম্যাট: `/adduser USER_ID`", parse_mode="Markdown")
        return
    try:
        new_id = int(context.args[0])
        if new_id in USERS:
            await update.message.reply_text("ℹ️ এই ইউজার আগেই অনুমোদিত রয়েছে।")
        else:
            USERS[new_id] = 0.0  # নতুন ইউজারের প্রারম্ভিক ব্যালেন্স 0.0
            await update.message.reply_text(f"✅ ইউজার সফলভাবে যুক্ত হয়েছে: `{new_id}`", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ আইডি অবশ্যই একটি সংখ্যা হতে হবে।")

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ ফরম্যাট: `/addbalance USER_ID AMOUNT`", parse_mode="Markdown")
        return
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])
        if target_id not in USERS:
            await update.message.reply_text("❌ ইউজারটি সিস্টেমে নেই! আগে `/adduser` দিন।", parse_mode="Markdown")
        else:
            USERS[target_id] += amount
            await update.message.reply_text(f"💳 `{target_id}` এর অ্যাকাউন্টে **${amount}** যোগ করা হয়েছে!\nবর্তমান ব্যালেন্স: **${USERS[target_id]}**", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ সঠিক ID ও Amount দিন। (যেমন: `/addbalance 123456 5.5`)", parse_mode="Markdown")

# --- MESSAGE & ACTION HANDLERS ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user(user_id):
        return

    text = update.message.text

    # User Balance Check
    if text in ["💳 Balance", "/balance"]:
        bal = USERS.get(user_id, 0.0)
        await update.message.reply_text(f"💳 **আপনার বর্তমান ব্যালেন্স:** ${bal:.2f}", parse_mode="Markdown", reply_markup=get_keyboard(user_id))

    # Number Purchase Menu
    elif text in ["📱 Get Number", "/getnum"]:
        inline_keyboard = [
            [InlineKeyboardButton("🇪🇬 Egypt (Telegram Low Rate)", callback_data="country_4")],
            [InlineKeyboardButton("🇮🇩 Indonesia (Telegram Low Rate)", callback_data="country_6")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await update.message.reply_text("দেশ সিলেক্ট করুন (Telegram Low Rate):", reply_markup=reply_markup)

    # Admin Panel (Only for Admins)
    elif text == "⚙️ Admin Panel" and is_admin(user_id):
        admin_keyboard = [
            [InlineKeyboardButton("💳 Check API Balance", callback_data="admin_balance")],
            [InlineKeyboardButton("👥 User List & Balances", callback_data="admin_list")]
        ]
        reply_markup = InlineKeyboardMarkup(admin_keyboard)
        msg_text = (
            "⚙️ **অ্যাডমিন প্যানেল কমান্ডস:**\n\n"
            "• ইউজার যোগ: `/adduser USER_ID`\n"
            "• ব্যালেন্স দিতে: `/addbalance USER_ID AMOUNT`"
        )
        await update.message.reply_text(msg_text, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not is_user(user_id):
        return

    data = query.data

    # Handling Country Selection
    if data.startswith("country_"):
        country_code = data.split("_")[1]
        
        # ব্যালেন্স চেক (ধরুন প্রতি নম্বরের খরচ $0.20)
        cost = 0.20
        if USERS.get(user_id, 0.0) < cost:
            await query.message.reply_text(f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই! প্রয়োজন: ${cost:.2f}", reply_markup=get_keyboard(user_id))
            return

        response = requests.get(HERO_BASE_URL, params={
            "api_key": HERO_API_KEY,
            "action": "getNumber",
            "service": "tg",
            "country": country_code
        })

        if "ACCESS_NUMBER" in response.text:
            USERS[user_id] -= cost  # ইউজারের অ্যাকাউন্ট থেকে টাকা কাটা
            res_data = response.text.split(":")
            await query.message.reply_text(
                f"📱 **নতুন নম্বর:** `{res_data[2]}`\n**আইডি:** `{res_data[1]}`\n\n💸 কাটা হয়েছে: ${cost:.2f}", 
                parse_mode="Markdown", 
                reply_markup=get_keyboard(user_id)
            )
        else:
            await query.message.reply_text(f"❌ নম্বর পাওয়া যায়নি: {response.text}", reply_markup=get_keyboard(user_id))

    # Admin Callback Actions
    elif is_admin(user_id):
        if data == "admin_balance":
            response = requests.get(HERO_BASE_URL, params={"api_key": HERO_API_KEY, "action": "getBalance"})
            bal = response.text.split(":")[1] if "ACCESS_BALANCE" in response.text else response.text
            await query.message.reply_text(f"⚙️ HeroSMS API Balance: ${bal}")

        elif data == "admin_list":
            user_text = "👥 **ইউজার তালিকা ও ব্যালেন্স:**\n" + "\n".join([f"• `{uid}` : ${bal:.2f}" for uid, bal in USERS.items()])
            await query.message.reply_text(user_text, parse_mode="Markdown")

if __name__ == '__main__':
    Thread(target=run_web).start()
    bot = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("balance", handle_message))
    bot.add_handler(CommandHandler("getnum", handle_message))
    bot.add_handler(CommandHandler("adduser", add_user))
    bot.add_handler(CommandHandler("addbalance", add_balance))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    bot.add_handler(CallbackQueryHandler(handle_callback_query))
    
    bot.run_polling()
