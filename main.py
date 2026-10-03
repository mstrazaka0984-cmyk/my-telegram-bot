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

# --- টোকেন ও এপিআই কনফিগারেশন ---
TELEGRAM_BOT_TOKEN = "8789966847:AAH0RMLgxUyEFsmgwcujFHrtvX6eel7yecg"
GOLDEN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3OTEwMTg0ODEsInN1YiI6InJha2liMDAwNSIsImFwaVRva2VuSWQiOiIxY2EwNWM4Yy02ZjZhLTQ0ODAtOTAyMS1lM2E2ODU0MDM0MDQifQ.WuZX6ykjk2n94Fa7y_7CWZ74Uio7t-iWGbUTF2X95K0"
GOLDEN_BASE_URL = "https://world-premium-telecom.com"

HEADERS = {
    "Authorization": f"Bearer {GOLDEN_TOKEN}",
    "Content-Type": "application/json"
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
            await update.message.reply_text(f"🗑️ ইউজার সফলতার সাথে رিমুভ করা হয়েছে: `{target_id}`", parse_mode="Markdown")
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
            [InlineKeyboardButton("💬 WhatsApp Code", callback_data="select_whatsapp")],
            [InlineKeyboardButton("✈️ Telegram Code", callback_data="select_telegram")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await update.message.reply_text("কোন অ্যাপের ভেরিফিকেশনের জন্য নম্বর প্রয়োজন? সিলেক্ট করুন:", reply_markup=reply_markup)

    elif text == "⚙️ Admin Panel" and is_admin(user_id):
        admin_keyboard = [
            [InlineKeyboardButton("💳 Check API Connection", callback_data="admin_balance")],
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
    cost = 0.20

    if data in ["select_whatsapp", "select_telegram"]:
        if USERS.get(user_id, 0.0) < cost:
            await query.message.reply_text(f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই! প্রয়োজন: ${cost:.2f}", reply_markup=get_keyboard(user_id))
            return

        response = requests.get(f"{GOLDEN_BASE_URL}/numbers", headers=HEADERS)

        if response.status_code == 200:
            res_json = response.json()
            if res_json and "data" in res_json and len(res_json["data"]) > 0:
                target_data = res_json["data"][0] if isinstance(res_json["data"], list) else res_json["data"]
                number = target_data.get("number")
                act_id = number
                
                USERS[user_id] -= cost

                action_buttons = [
                    [
                        InlineKeyboardButton("🔄 Check OTP", callback_data=f"check_{act_id}"),
                        InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{act_id}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(action_buttons)

                service_name = "WhatsApp" if data == "select_whatsapp" else "Telegram"
                await query.message.reply_text(
                    f"📱 **নতুন নম্বর ({service_name}):** `{number}`\n\n⏳ নম্বরটি কপি করে আপনার অ্যাপে বসিয়ে কোড পাঠান। এরপর নিচের **Check OTP** বাটনে ক্লিক করুন।\n\n💸 কাটা হয়েছে: ${cost:.2f}",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            else:
                await query.message.reply_text("❌ এই মুহূর্তে প্যানেলে কোনো লাইভ নম্বর খালি নেই। একটু পর চেষ্টা করুন।", reply_markup=get_keyboard(user_id))
        else:
            await query.message.reply_text("❌ এপিআই সার্ভার থেকে নম্বর রেসপন্স পাওয়া যায়নি।", reply_markup=get_keyboard(user_id))

    elif data.startswith("check_"):
        act_id = data.split("_")[1]
        response = requests.get(f"{GOLDEN_BASE_URL}/active-calls", headers=HEADERS)
        
        otp_found = False
        if response.status_code == 200:
            res_json = response.json()
            if "data" in res_json and isinstance(res_json["data"], list):
                for call in res_json["data"]:
                    if str(call.get("prn")) == str(act_id) or str(call.get("cli")) == str(act_id):
                        text_received = call.get("text", "") or call.get("msg", "")
                        if text_received:
                            await query.message.reply_text(f"✅ **আপনার OTP কোড / মেসেজ:**\n`{text_received}`", parse_mode="Markdown")
                            otp_found = True
                            break
            
            if not otp_found:
                await query.message.reply_text("⏳ এখনও কোনো ওটিপি কোড বা কল আসেনি, অ্যাপে কোড সেন্ড করে আবার ট্রাই করুন।")
        else:
            await query.message.reply_text("⚠️ ওটিপি সার্ভার চেক করা যাচ্ছে না।")

    elif data.startswith("cancel_"):
        act_id = data.split("_")[1]
        USERS[user_id] += cost
        await query.edit_message_text(f"❌ **নম্বর ক্যানসেল করা হয়েছে!**\n💳 ${cost:.2f} রিফান্ড দেওয়া হয়েছে।", parse_mode="Markdown")

    elif is_admin(user_id):
        if data == "admin_balance":
            response = requests.get(f"{GOLDEN_BASE_URL}/subaccounts", headers=HEADERS)
            if response.status_code == 200:
                await query.message.reply_text("⚙️ **Golden API Connection Status:** 🟢 Connected & Active")
            else:
                await query.message.reply_text(f"⚠️ এপিআই সংযোগে ত্রুটি। কোড: {response.status_code}")
    
