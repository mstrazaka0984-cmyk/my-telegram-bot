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

# ১. মাস্টার অ্যাডমিন তালিকা
ADMINS = [6282253982, 8600579923]

# ২. অনুমোদিত ইউজার তালিকা ও ব্যালেন্স ডাটাবেস
USERS = {
    6282253982: 100.0,
    8600579923: 100.0
}

TELEGRAM_BOT_TOKEN = "8789966847:AAH0RMLgxUyEFsmgwcujFHrtvX6eel7yecg"
HERO_API_KEY = "d038528eA9dAf95998A99c70de23e695"
HERO_BASE_URL = "https://hero-sms.com/stubs/handler_api.php"

# দেশ ও API ID ম্যাপ (HeroSMS অনুযায়ী)
COUNTRIES = {
    "187": "🇪🇨 Ecuador",
    "37": "🇲🇦 Morocco",
    "12": "🇺🇸 USA",
    "20": "🇪🇬 Egypt",
    "6": "🇮🇩 Indonesia",
    "22": "🇮🇳 India",
    "16": "🇬🇧 UK",
    "32": "🇷🇺 Russia"
}

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def is_user(user_id: int) -> bool:
    return user_id in USERS

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
        if new_id in USERS:
            await update.message.reply_text("ℹ️ এই ইউজার আগেই অনুমোদিত রয়েছে।")
        else:
            USERS[new_id] = 0.0
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
        elif target_id in USERS:
            del USERS[target_id]
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
        if target_id not in USERS:
            await update.message.reply_text("❌ ইউজারটি সিস্টেমে নেই! আগে `/adduser` দিন।", parse_mode="Markdown")
        else:
            USERS[target_id] += amount
            await update.message.reply_text(f"💳 `{target_id}` এর অ্যাকাউন্টে **${amount}** যোগ করা হয়েছে!\nবর্তমান ব্যালেন্স: **${USERS[target_id]}**", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ সঠিক ID ও Amount দিন। (যেমন: `/addbalance 123456 5.5`)", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user(user_id):
        return

    text = update.message.text

    if text in ["💳 Balance", "/balance"]:
        bal = USERS.get(user_id, 0.0)
        await update.message.reply_text(f"💳 **আপনার বর্তমান ব্যালেন্স:** ${bal:.2f}", parse_mode="Markdown", reply_markup=get_keyboard(user_id))

    elif text in ["📱 Get Number", "/getnum"]:
        inline_keyboard = [
            [InlineKeyboardButton("✈️ Telegram", callback_data="service_tg")],
            [InlineKeyboardButton("💬 WhatsApp", callback_data="service_wa")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await update.message.reply_text("প্লিজ সার্ভিস সিলেক্ট করুন:", reply_markup=reply_markup)

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

    if data.startswith("service_"):
        service_code = data.split("_")[1] # tg or wa
        service_name = "Telegram" if service_code == "tg" else "WhatsApp"

        inline_keyboard = []
        for cid, name in COUNTRIES.items():
            inline_keyboard.append([InlineKeyboardButton(name, callback_data=f"buy_{service_code}_{cid}")])

        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await query.message.reply_text(f"**{service_name}**-এর জন্য দেশ সিলেক্ট করুন:", parse_mode="Markdown", reply_markup=reply_markup)

    elif data.startswith("buy_"):
        _, service_code, country_code = data.split("_")
        cost = 0.20
        country_name = COUNTRIES.get(country_code, country_code)
        
        if USERS.get(user_id, 0.0) < cost:
            await query.message.reply_text(f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই! প্রয়োজন: ${cost:.2f}", reply_markup=get_keyboard(user_id))
            return

        response = requests.get(HERO_BASE_URL, params={
            "api_key": HERO_API_KEY,
            "action": "getNumber",
            "service": service_code,
            "country": country_code
        })

        if "ACCESS_NUMBER" in response.text:
            USERS[user_id] -= cost
            res_data = response.text.split(":")
            act_id = res_data[1]
            number = res_data[2]

            action_buttons = [
                [
                    InlineKeyboardButton("🔄 Check OTP", callback_data=f"check_{act_id}"),
                    InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{act_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(action_buttons)

            await query.message.reply_text(
                f"📱 **নতুন নম্বর ({country_name}):** `{number}`\n🆔 **আইডি:** `{act_id}`\n\n💸 কাটা হয়েছে: ${cost:.2f}", 
                parse_mode="Markdown", 
                reply_markup=reply_markup
            )
        else:
            await query.message.reply_text(f"❌ নম্বর পাওয়া যায়নি: {response.text}", reply_markup=get_keyboard(user_id))

    elif data.startswith("check_"):
        act_id = data.split("_")[1]
        response = requests.get(HERO_BASE_URL, params={"api_key": HERO_API_KEY, "action": "getStatus", "id": act_id})
        
        if "STATUS_OK" in response.text:
            code = response.text.split(":")[1]
            await query.message.reply_text(f"✅ **আপনার OTP কোড:** `{code}`", parse_mode="Markdown")
        elif "STATUS_WAIT_CODE" in response.text:
            await query.message.reply_text("⏳ এখনও কোড আসেনি, কিছুক্ষণ পর আবার ট্রাই করুন।")
        else:
            await query.message.reply_text(f"ℹ️ স্ট্যাটাস: {response.text}")

    elif data.startswith("cancel_"):
        act_id = data.split("_")[1]
        response = requests.get(HERO_BASE_URL, params={"api_key": HERO_API_KEY, "action": "setStatus", "id": act_id, "status": "8"})

        if "ACCESS_CANCEL" in response.text or "ACCESS_SUCCESS" in response.text:
            USERS[user_id] += 0.20
            await query.edit_message_text(f"❌ **নম্বর ক্যানসেল করা হয়েছে!**\n💳 $0.20 রিফান্ড দেওয়া হয়েছে।", parse_mode="Markdown")
        else:
            await query.message.reply_text(f"⚠️ ক্যানসেল করা যায়নি: {response.text}")

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
    bot.add_handler(CommandHandler("deluser", del_user))
    bot.add_handler(CommandHandler("addbalance", add_balance))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    bot.add_handler(CallbackQueryHandler(handle_callback_query))
    
    bot.run_polling()
