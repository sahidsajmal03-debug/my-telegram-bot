import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Logging সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


# "8822026636:AAF8eCJbYCvU1T79HuVh_Ioxnf2rbRicq0M"
 ==============================================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8822026636:AAF8eCJbYCvU1T79HuVh_Ioxnf2rbRicq0M")

# ==============================================================================
# "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"
# ==============================================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

# Groq Client ইনিশিয়ালাইজেশন
client = Groq(api_key=GROQ_API_KEY)

# /start কমান্ড
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("হ্যালো! আমি Groq AI দ্বারা চালিত আপনার অ্যাসিস্ট্যান্ট। আমাকে যেকোনো প্রশ্ন করতে পারেন।")

# মেসেজ হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_text}
            ]
        )
        bot_reply = response.choices[0].message.content
        await update.message.reply_text(bot_reply)
    except Exception as e:
        await update.message.reply_text(f"একটি ত্রুটি ঘটেছে: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Groq Bot is running...")
    app.run_polling()
