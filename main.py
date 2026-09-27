import os
import requests
import re
from flask import Flask, request, jsonify
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

app_web = Flask('')

# ১. মাস্টার অ্যাডমিন তালিকা
ADMINS = [6282253982, 8600579923]

# ২. অনুমোদিত ইউজার তালিকা ও ব্যালেন্স ডাটাবেস
USERS = {
    6282253982: 100.0,
    8600579923: 100.0
}

# ৩. অ্যাক্টিভ সেশন ট্র্যাকার (কোন নম্বর কোন ইউজার ব্যবহার করছে)
ACTIVE_SESSIONS = {}

TELEGRAM_BOT_TOKEN = "8789966847:AAH0RMLgxUyEFsmgwcujFHrtvX6eel7yecg"

# ৪. মাল্টি-কান্ট্রি নম্বর পুল (দেশ অনুযায়ী নম্বর আলাদা রাখার ডিকশনারি)
NUMBER_POOLS = {
    "ecuador": [],
    "egypt": [],
    "indonesia": []
}

# ৫. ওটিপি ভয়েস টেক্সট থেকে সংখ্যা ফিল্টার করার ফাংশন
def text_to_digits(text):
    word_to_digit = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9'
    }
    digits = []
    words = re.findall(r'\b\w+\b', text.lower())
    for word in words:
        if word in word_to_digit:
            digits.append(word_to_digit[word])
    return "".join(digits) if digits else None

# ৬. Orange Carrier এর ইনকামিং ভয়েস কল ওয়েবহুক রাউট
@app_web.route('/api/voice-callback', methods=['POST'])
def voice_callback():
    data = request.json
    incoming_number = data.get('to_number') 
    
    if incoming_number in ACTIVE_SESSIONS:
        user_id = ACTIVE_SESSIONS[incoming_number]
        
        try:
            voice_text = data.get('transcription_text', "")
            otp_code = text_to_digits(voice_text)
            
            if otp_code:
                bot_url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
                msg_payload = {
                    "chat_id": user_id,
                    "text": f"📞 **OTP Received**\n`{incoming_number}`\n\n_\"{voice_text}\"_\n\n🔑 `{otp_code}`",
                    "parse_mode": "Markdown"
                }
                requests.post(bot_url, json=msg_payload)
                del ACTIVE_SESSIONS[incoming_number]
        except Exception as e:
            print(f"Error processing Voice OTP: {e}")
            
    return jsonify({"status": "success"}), 200

@app_web.route('/')
def home():
    return "Bot is running with Multi-Country Admin Number Manager!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- টেলিগ্রাম বটের মূল কোড পার্ট ---

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
        await update.message.reply_text(f"⛔ দুঃখিত! আপনার সার্ভিস ব্যবহারের অনুমতি নেই।\n**Telegram ID:** `{user_id}`", parse_mode="Markdown")
        return
    await update.message.reply_text("স্বাগতম! 👋\nনিচের MENU থেকে আপনার প্রয়োজনীয় অপশন সিলেক্ট করুন:", reply_markup=get_keyboard(user_id))

# ⚙️ অ্যাডমিন কমান্ড ১: দেশের নাম উল্লেখ করে নম্বর যোগ করা
async def add_bulk_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ **সঠিক ফরম্যাট:** `/addnum [দেশের_নাম] [নম্বর১,নম্বর২]`\n\n"
            "**উদাহরণ:** `/addnum ecuador +593962854970,+593962855003`\n"
            "*(দেশের নাম ছোট হাতের অক্ষরে স্পেস ছাড়া লিখবেন)*", 
            parse_mode="Markdown"
        )
        return
    
    country = context.args[0].lower()
    raw_numbers_input = context.args[1]
    raw_numbers = raw_numbers_input.split(",")
    
    if country not in NUMBER_POOLS:
        NUMBER_POOLS[country] = []
        
    added_count = 0
    for num in raw_numbers:
        clean_num = num.strip()
        if clean_num and clean_num not in NUMBER_POOLS[country]:
            NUMBER_POOLS[country].append(clean_num)
            added_count += 1
            
    await update.message.reply_text(
        f"✅ সফলভাবে **{country.upper()}** দেশে **{added_count}** টি নতুন নম্বর যোগ করা হয়েছে!\n"
        f"📊 এই দেশে বর্তমান মোট নম্বর: **{len(NUMBER_POOLS[country])}**", 
        parse_mode="Markdown"
    )

# ⚙️ অ্যাডমিন কমান্ড ২: নির্দিষ্ট দেশের নম্বর রিসেট করা
async def clear_all_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("⚠️ **ফরম্যাট:** `/clear_numbers [দেশের_নাম]` (যেমন: `/clear_numbers ecuador`)")
        return
    
    country = context.args[0].lower()
    if country in NUMBER_POOLS:
        NUMBER_POOLS[country] = []
        await update.message.reply_text(f"🗑️ **{country.upper()}** দেশের সব পুরনো নম্বর সফলভাবে মুছে ফেলা হয়েছে!")
    else:
        await update.message.reply_text("❌ এই নামের কোনো দেশ ডাটাবেজে পাওয়া যায়নি।")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user(user_id): return
    text = update.message.text

    if text in ["💳 Balance", "/balance"]:
        bal = USERS.get(user_id, 0.0)
        await update.message.reply_text(f"💳 **আপনার বর্তমান ব্যালেন্স:** \${bal:.2f}", parse_mode="Markdown", reply_markup=get_keyboard(user_id))

    elif text in ["📱 Get Number", "/getnum"]:
        inline_keyboard = [
            [InlineKeyboardButton("🇪🇨 Ecuador (Voice / IVR)", callback_data="get_ecuador")],
            [InlineKeyboardButton("🇪🇬 Egypt (Voice / IVR)", callback_data="get_egypt")],
            [InlineKeyboardButton("🇮🇩 Indonesia (Voice / IVR)", callback_data="get_indonesia")]
        ]
        await update.message.reply_text("দেশ সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard))

    elif text == "⚙️ Admin Panel" and is_admin(user_id):
        msg_text = (
            "⚙️ **অ্যাডমিন প্যানেল কমান্ডস:**\n\n"
            "• ইউজার যোগ: `/adduser USER_ID`\n"
            "• ব্যালেন্স দিতে: `/addbalance USER_ID AMOUNT`\n"
            "• 🆕 **দেশসহ নম্বর যোগ:** `/addnum ecuador +59312345,+59367890`\n"
            "• 🆕 **নির্দিষ্ট দেশের নম্বর ডিলিট:** `/clear_numbers ecuador`"
        )
        await update.message.reply_text(msg_text, parse_mode="Markdown")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not is_user(user_id): return
    
    cost = 0.15  # প্রতি নম্বর চার্জ ১৫ সেন্ট

    target_country = ""
    if query.data == "get_ecuador": target_country = "ecuador"
    elif query.data == "get_egypt": target_country = "egypt"
    elif query.data == "get_indonesia": target_country = "indonesia"

    if target_country:
        if USERS.get(user_id, 0.0) < cost:
            await query.message.reply_text(f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই! প্রয়োজন: \${cost:.2f}")
            return
        
        country_pool = NUMBER_POOLS.get(target_country, [])
        if len(country_pool) == 0:
            await query.message.reply_text(f"❌ দুঃখিত! এই মুহূর্তে **{target_country.upper()}** এর পুলে কোনো নম্বর নেই।")
            return

        numbers_to_show = country_pool[:5] 
        
        msg_text = f"📱 **আপনার জন্য {target_country.upper()} এর নম্বর রেঞ্জ:**\n\n"
        for num in numbers_to_show:
            msg_text += f"📋 `{num}`\n"
            ACTIVE_SESSIONS[num] = user_id
            
        USERS[user_id] -= cost 
        msg_text += f"\n💸 কাটা হয়েছে: \${cost:.2f}\n\n💡 _যেকোনো একটি নম্বর কপি করে কাজ শুরু করুন। কোড অটোমেটিক চলে আসবে।_"
        
        await query.message.reply_text(msg_text, parse_mode="Markdown")

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    new_id = int(context.args[0])
    USERS[new_id] = 0.0
    await update.message.reply_text(f"✅ ইউজার সফলভাবে যুক্ত হয়েছে: `{new_id}`")

def main():
    Thread(target=run_web).start()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("addnum", add_bulk_numbers))
    app.add_handler(CommandHandler("clear_numbers", clear_all_numbers))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    print("Bot is alive and running...")
    app.run_polling()

if __name__ == '__main__':
    main()
