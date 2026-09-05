import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Logging সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Render Environment Variables থেকে টোকেন সংগ্রহ
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# ==============================================================================
# এখানে আপনার টেলিগ্রাম বটের User Name বসান (যেমন: "@your_bot_username")
# ==============================================================================
BOT_USERNAME = "@your_bot_username"  # <-- এখানে আপনার বটের Username বসাবেন

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("হ্যালো! আমি Groq AI দ্বারা চালিত আপনার অ্যাসিস্ট্যান্ট। আমাকে গ্রুপে ট্যাগে/রিপ্লাইতে বা প্রাইভেটে যেকোনো প্রশ্ন করতে পারেন।")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_type = update.message.chat.type
    user_text = update.message.text
    bot_info = await context.bot.get_me()
    bot_id = bot_info.id
    bot_username = f"@{bot_info.username}" if bot_info.username else BOT_USERNAME

    # ১. প্রাইভেট চ্যাটে (Direct Message) সব মেসেজের উত্তর দেবে
    if chat_type == "private":
        should_respond = True
        prompt_text = user_text
    else:
        # ২. গ্রুপ বা সুপারগ্রুপ চ্যাট হলে শর্ত চেক করা হবে:
        is_mentioned = bot_username.lower() in user_text.lower()
        
        # মেসেজটি বটের কোনো আগের মেসেজের রিপ্লাই কি না চেক
        is_reply_to_bot = (
            update.message.reply_to_message is not None and
            update.message.reply_to_message.from_user is not None and
            update.message.reply_to_message.from_user.id == bot_id
        )

        # কেবল ম্যানশন করা হলে বা বটের মেসেজে রিপ্লাই দিলেই রেসপন্স করবে
        if is_mentioned or is_reply_to_bot:
            should_respond = True
            # প্রম্পট থেকে বটের ইউজারনেম ফিল্টার করে নেওয়া
            prompt_text = user_text.replace(bot_username, "").strip()
        else:
            should_respond = False

    # শর্ত না মিললে কোনো রেসপন্স করবে না
    if not should_respond:
        return

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_text if prompt_text else user_text}
            ]
        )
        bot_reply = response.choices[0].message.content
        await update.message.reply_text(bot_reply)
    except Exception as e:
        await update.message.reply_text(f"একটি ত্রুটি ঘটেছে: {str(e)}")

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
