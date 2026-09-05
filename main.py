import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# নতুন Telegram Bot Token এবং OpenAI API Key
TELEGRAM_BOT_TOKEN = "8644242747:AAFINNnjOK3WgxmVxouC5dx92GSf2jGXx0I"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "Sk-proj-TWfWUZ0cAaV5WZkKL2k_BignTPYRJDYbjXY11WLqhbX38koNkwySdhzDxDMiJvntIAHi2jCeUcT3BlbkFJp8kfpVuVQmjETBuEsUJiQcEkU_idyoFCLdJhSylTi11jS4J22AsDbxfGd6snovBoc0AsERDHYA")

# OpenAI Client সেটআপ
client = OpenAI(api_key=OPENAI_API_KEY)

# /start কমান্ড
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("হ্যালো! আমি আপনার AI অ্যাসিস্ট্যান্ট। আমাকে যেকোনো প্রশ্ন করতে পারেন।")

# মেসেজ প্রসেস এবং উত্তর দেওয়ার ফাংশন
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
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
    
    print("Bot is running...")
    app.run_polling()
