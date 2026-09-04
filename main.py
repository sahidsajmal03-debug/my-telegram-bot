import logging
import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

TELEGRAM_BOT_TOKEN = "8862094941:AAFOYsVjpW4U35_vapq1JwjvCYMOYKd5voI"
GEMINI_API_KEY = "AQ.Ab8RN6I_ruo9d0J0K3-rJbpK3A7DpjbeLhFm8RgGtFPxp1_XKA"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Hello! I am your AI Assistant powered by Gemini.\n\n"
        "To get a response from me in a group, please **mention me** (e.g. @Gimini100_Bot) "
        "or **reply to my messages**!"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def reply_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    bot_username = context.bot.username
    user_text = update.message.text
    
    is_mentioned = f"@{bot_username}" in user_text
    is_reply_to_bot = (
        update.message.reply_to_message and 
        update.message.reply_to_message.from_user.id == context.bot.id
    )

    if not (is_mentioned or is_reply_to_bot):
        return

    clean_text = user_text.replace(f"@{bot_username}", "").strip()
    if not clean_text:
        clean_text = "Hello"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": clean_text}]
        }]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                res_data = await response.json()
                
                if 'candidates' in res_data and len(res_data['candidates']) > 0:
                    ai_reply = res_data['candidates'][0]['content']['parts'][0]['text']
                    await update.message.reply_text(ai_reply)
                else:
                    print("Gemini API Error:", res_data)

    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), reply_to_group)
    app.add_handler(text_handler)

    print("Fast Bot is running...")
    app.run_polling()
