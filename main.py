import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Logging সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Render Environment Variables থেকে টোকেন ও API Key সংগ্রহ করা হচ্ছে
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Groq Client ইনিশিয়ালাইজেশন
client = Groq(api_key=GROQ_API_KEY)

# ==============================================================================
# Render-এর Web Service Port Scan Timeout সমাধানের জন্য ফেক/ডামি ওয়েবাসার্ভার
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
    await update.message.reply_text("হ্যালো! আমি Groq AI দ্বারা চালিত আপনার অ্যাসিস্ট্যান্ট। আমাকে যেকোনো প্রশ্ন করতে পারেন।")

# মেসেজ প্রসেস এবং Groq AI থেকে উত্তর সংগ্রহ করার ফাংশন
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",  # আপডেটেড ও সক্রিয় মডেল
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_text}
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
    # ব্যাকগ্রাউন্ড থ্রেডে ডামি সার্ভার চালু করা (যা Render-এর পোর্ট এরর আটকাবে)
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # টেলিগ্রাম বট অ্যাপ সেটআপ
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Groq Bot is running securely on Render Free Web Service...")
    app.run_polling()
