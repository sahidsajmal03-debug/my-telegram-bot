import os
import logging
import asyncio
import aiohttp
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Hardcoded Credentials
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
    
    # Check private chat OR mention/reply in group
    is_private = update.message.chat.type == 'private'
    is_mentioned = f"@{bot_username}" in user_text
    is_reply_to_bot = (
        update.message.reply_to_message and 
        update.message.reply_to_message.from_user.id == context.bot.id
    )

    if not (is_private or is_mentioned or is_reply_to_bot):
        return

    clean_text = user_text.replace(f"@{bot_username}", "").strip()
    if not clean_text:
        clean_text = "Hello"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
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
                    logging.error(f"Gemini Error: {res_data}")

    except Exception as e:
        logging.error(f"Exception: {e}")

# Dummy Web Server to keep Render Web Service active
async def handle_ping(request):
    return web.Response(text="Bot is Alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await start_web_server()
    
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), reply_to_group))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    print("Bot is successfully running...")
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
