import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Logging সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Render Environment Variables থেকে টোকেন ও Key সংগ্রহ
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Groq Client ইনিশিয়ালাইজেশন
client = Groq(api_key=GROQ_API_KEY)

# ==============================================================================
# Render Web Service Port Scan Timeout সমাধানের জন্য ডামি সার্ভার
# ==============================================================================
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running 24/7!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# ==============================================================================
# Telegram Bot Handlers
# ==============================================================================

# /start কমান্ড হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Ami apnar AI assistant. Shadharon uttor maximum 120 words-er hobe, aar /all likhle pura vistarito uttor paben.")

# মেসেজ প্রসেস এবং Groq AI থেকে উত্তর সংগ্রহ করার ফাংশন
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_type = update.message.chat.type
    raw_user_text = update.message.text
    bot_info = await context.bot.get_me()
    bot_id = bot_info.id
    bot_username = f"@{bot_info.username}" if bot_info.username else ""

    # ১. প্রাইভেট চ্যাটে সরাসরি উত্তর দেবে
    if chat_type == "private":
        should_respond = True
        prompt_text = raw_user_text
    else:
        # ২. গ্রুপ বা সুপারগ্রুপে কেবল ম্যানশন বা রিপ্লাই দিলে উত্তর দেবে
        is_mentioned = bot_username.lower() in raw_user_text.lower() if bot_username else False
        
        is_reply_to_bot = (
            update.message.reply_to_message is not None and
            update.message.reply_to_message.from_user is not None and
            update.message.reply_to_message.from_user.id == bot_id
        )

        if is_mentioned or is_reply_to_bot:
            should_respond = True
            prompt_text = raw_user_text.replace(bot_username, "").strip() if bot_username else raw_user_text
        else:
            should_respond = False

    if not should_respond:
        return

    # /all ফ্ল্যাগ চেক করা
    has_all_flag = "/all" in prompt_text.lower()
    
    # প্রম্পট থেকে /all নির্দেশক মুছে ফেলা
    clean_prompt = prompt_text.replace("/all", "").replace("/ALL", "").strip()
    if not clean_prompt:
        clean_prompt = prompt_text

    # /all থাকলে শব্দের সীমার তুলে দেওয়া হবে, অন্যথায় সর্বোচ্চ ১২০ শব্দের মধ্যে থাকবে
    if has_all_flag:
        length_instruction = "Give a detailed and complete answer without word limit restrictions."
    else:
        length_instruction = "CRITICAL LIMIT: Keep your response STRICTLY UNDER 120 WORDS. Be clear and concise."

    system_prompt = (
        "You are a helpful assistant. Reply in the SAME LANGUAGE as the user's input/question. "
        "CRITICAL RULE: Always write your output using ONLY English letters (Latin/Roman script). "
        "Never use native non-English scripts like Bangla, Hindi, Arabic, Japanese, Chinese, Cyrillic, etc. "
        f"{length_instruction}"
    )

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": clean_prompt}
            ]
        )
        bot_reply = response.choices[0].message.content

        # /all না থাকলে বাড়তি সুরক্ষার জন্য ১২০ শব্দে ট্রাঙ্কেট/কাট করার চেষ্টা
        if not has_all_flag:
            words = bot_reply.split()
            if len(words) > 120:
                bot_reply = " ".join(words[:120]) + "..."

        await update.message.reply_text(bot_reply)
    except Exception as e:
        await update.message.reply_text(f"Ekta error hoyeche: {str(e)}")

# ==============================================================================
# Main Execution
# ==============================================================================
if __name__ == '__main__':
    # ব্যাকগ্রাউন্ড থ্রেডে ডামি সার্ভার চালু রাখা
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Groq Bot is running securely on Render Free Web Service...")
    app.run_polling()
