import os
import sqlite3
import aiohttp
import requests
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- FLASK KEEP-ALIVE SERVER ---
app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- CONFIGURATIONS ---
ADMINS = [6282253982, 8600579923]
TELEGRAM_BOT_TOKEN = "8789966847:AAH0RMLgxUyEFsmgwcujFHrtvX6eel7yecg"
HERO_API_KEY = "d038528eA9dAf95998A99c70de23e695"
HERO_BASE_URL = "https://hero-sms.com/stubs/handler_api.php"

# --- SQLITE DATABASE SETUP ---
DB_NAME = "bot_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
    ''')
    for admin_id in ADMINS:
        cursor.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)', (admin_id, 100.0))
    conn.commit()
    conn.close()

def get_db_user_balance(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def add_db_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0.0))
    conn.commit()
    conn.close()

def delete_db_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def update_db_balance(user_id: int, amount: float):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def get_all_db_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, balance FROM users')
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- HELPER FUNCTIONS ---
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def is_user(user_id: int) -> bool:
    return get_db_user_balance(user_id) is not None

def get_keyboard(user_id: int):
    if is_admin(user_id):
        keyboard = [
            [KeyboardButton("📱 Get Number"), KeyboardButton("💳 Balance")],
            [KeyboardButton("⚙️ Admin Panel")]
        ]
    else:
        keyboard = [
            [KeyboardButton("📱 Get Number"), KeyboardButton("💳 Balance")]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- BOT COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user(user_id):
        await update.message.reply_text(f"⛔ দুঃখিত! আপনার সার্ভিস ব্যবহারের অনুমতি নেই।\nআপনার Telegram ID: `{user_id}`", parse_mode="Markdown")
        return
    
    await update.message.reply_text(
        "স্বাগতম! 👋\nনিচের MENU থেকে আপনার প্রয়োজনীয় অপশন সিলেক্ট করুন:",
        reply_markup=get_keyboard(user_id)
    )

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("⚠️ ফরম্যাট: `/adduser USER_ID`", parse_mode="Markdown")
        return
    try:
        new_id = int(context.args[0])
        if is_user(new_id):
            await update.message.reply_text("ℹ️ এই ইউজার আগেই অনুমোদিত রয়েছে।")
        else:
            add_db_user(new_id)
            await update.message.reply_text(f"✅ ইউজার সফলভাবে যুক্ত হয়েছে: `{new_id}`", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ আইডি অবশ্যই একটি সংখ্যা হতে হবে।")

async def del_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("⚠️ ফরম্যাট: `/deluser USER_ID`", parse_mode="Markdown")
        return
    try:
        target_id = int(context.args[0])
        if target_id in ADMINS:
            await update.message.reply_text("⛔ আপনি কোনো অ্যাডমিনকে বাদ দিতে পারবেন না!")
        elif is_user(target_id):
            delete_db_user(target_id)
            await update.message.reply_text(f"🗑️ ইউজার সফলতার সাথে রিমুভ করা হয়েছে: `{target_id}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ এই আইডিটি ইউজার তালিকায় নেই।")
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
        if not is_user(target_id):
            await update.message.reply_text("❌ ইউজারটি সিস্টেমে নেই! আগে `/adduser` দিন।", parse_mode="Markdown")
        else:
            update_db_balance(target_id, amount)
            current_bal = get_db_user_balance(target_id)
            await update.message.reply_text(f"💳 `{target_id}` এর অ্যাকাউন্টে **${amount:.2f}** যোগ করা হয়েছে!\nবর্তমান ব্যালেন্স: **${current_bal:.2f}**", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ সঠিক ID ও Amount দিন। (যেমন: `/addbalance 123456 5.5`)", parse_mode="Markdown")

# --- MESSAGE & ACTION HANDLERS ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user(user_id):
        return

    text = update.message.text

    if text in ["💳 Balance", "/balance"]:
        bal = get_db_user_balance(user_id)
        await update.message.reply_text(f"💳 **আপনার বর্তমান ব্যালেন্স:** ${bal:.2f}", parse_mode="Markdown", reply_markup=get_keyboard(user_id))

    elif text in ["📱 Get Number", "/getnum"]:
        inline_keyboard = [
            [InlineKeyboardButton("🇪🇬 Egypt (Telegram Low Rate)", callback_data="country_21")],
            [InlineKeyboardButton("🇮🇩 Indonesia (Telegram Low Rate)", callback_data="country_6")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await update.message.reply_text("দেশ সিলেক্ট করুন (Telegram Low Rate):", reply_markup=reply_markup)

    elif text == "⚙️ Admin Panel" and is_admin(user_id):
        admin_keyboard = [
            [InlineKeyboardButton("💳 Check API Balance", callback_data="admin_balance")],
            [InlineKeyboardButton("👥 User List & Balances", callback_data="admin_list")]
        ]
        reply_markup = InlineKeyboardMarkup(admin_keyboard)
        msg_text = (
            "⚙️ **অ্যাডমিন প্যানেল কমান্ডস:**\n\n"
            "• ইউজার যোগ: `/adduser USER_ID`\n"
            "• ইউজার রিমুভ: `/deluser USER_ID`\n"
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

    if data.startswith("country_"):
        country_code = data.split("_")[1]
        cost = 0.20
        
        user_bal = get_db_user_balance(user_id)
        if user_bal < cost:
            await query.message.reply_text(f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই! প্রয়োজন: ${cost:.2f}", reply_markup=get_keyboard(user_id))
            return

        async with aiohttp.ClientSession() as session:
            params = {
                "api_key": HERO_API_KEY,
                "action": "getNumber",
                "service": "tg",
                "country": country_code
            }
            async with session.get(HERO_BASE_URL, params=params) as resp:
                text_res = await resp.text()

        if "ACCESS_NUMBER" in text_res:
            update_db_balance(user_id, -cost)
            res_data = text_res.split(":")
            act_id = res_data[1]
            number = res_data[2]
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Check OTP", callback_data=f"check_{act_id}"),
                    InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{act_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.reply_text(
                f"📱 **নতুন নম্বর:** `{number}`\n🆔 **আইডি:** `{act_id}`\n\n💸 কাটা হয়েছে: ${cost:.2f}", 
                parse_mode="Markdown", 
                reply_markup=reply_markup
            )
        else:
            await query.message.reply_text(f"❌ নম্বর পাওয়া যায়নি: {text_res}", reply_markup=get_keyboard(user_id))

    elif data.startswith("check_"):
        act_id = data.split("_")[1]
        async with aiohttp.ClientSession() as session:
            params = {"api_key": HERO_API_KEY, "action": "getStatus", "id": act_id}
            async with session.get(HERO_BASE_URL, params=params) as resp:
                text_res = await resp.text()

        if "STATUS_OK" in text_res:
            code = text_res.split(":")[1]
            await query.message.reply_text(f"✅ **আপনার OTP কোড:** `{code}`", parse_mode="Markdown")
        elif "STATUS_WAIT_CODE" in text_res:
            await query.message.reply_text("⏳ এখনও কোড আসেনি, কিছুক্ষণ পর আবার চেষ্টা করুন।")
        else:
            await query.message.reply_text(f"ℹ️ স্ট্যাটাস: {text_res}")

    elif data.startswith("cancel_"):
        act_id = data.split("_")[1]
        async with aiohttp.ClientSession() as session:
            params = {"api_key": HERO_API_KEY, "action": "setStatus", "id": act_id, "status": "8"}
            async with session.get(HERO_BASE_URL, params=params) as resp:
                text_res = await resp.text()

        if "ACCESS_CANCEL" in text_res or "ACCESS_SUCCESS" in text_res:
            update_db_balance(user_id, 0.20)
            await query.edit_message_text(f"❌ **নম্বর ক্যানসেল করা হয়েছে!**\n💳 $0.20 রিফান্ড দেওয়া হয়েছে।", parse_mode="Markdown")
        else:
            await query.message.reply_text(f"⚠️ ক্যানসেল করা যায়নি: {text_res}")

    elif is_admin(user_id):
        if data == "admin_balance":
            async with aiohttp.ClientSession() as session:
                params = {"api_key": HERO_API_KEY, "action": "getBalance"}
                async with session.get(HERO_BASE_URL, params=params) as resp:
                    text_res = await resp.text()
            bal = text_res.split(":")[1] if "ACCESS_BALANCE" in text_res else text_res
            await query.message.reply_text(f"⚙️ HeroSMS API Balance: ${bal}")

        elif data == "admin_list":
            users = get_all_db_users()
            user_text = "👥 **ইউজার তালিকা ও ব্যালেন্স:**\n" + "\n".join([f"• `{uid}` : ${bal:.2f}" for uid, bal in users])
            await query.message.reply_text(user_text, parse_mode="Markdown")

if __name__ == '__main__':
    init_db()
    Thread(target=run_web).start()
    
    bot = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("balance", handle_message))
    bot.add_handler(CommandHandler("getnum", handle_message))
    bot.add_handler(CommandHandler("adduser", add_user))
    bot.add_handler(CommandHandler("deluser", del_user))
    bot.add_handler(CommandHandler("addbalance", add_balance))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    bot.add_handler(CallbackQueryHandler(handle_callback_query))
    
    bot.run_polling()
