import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from config import TOKEN
from downloader import download_video, download_audio

# --- البداية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 اهلا\n\n"
        "ارسل رابط فيديو من أي منصة وسأقوم بتحميله لك\n\n"
        "🎥 فيديو\n"
        "🎵 صوت"
    )

# --- استقبال الرابط ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    keyboard = [
        [InlineKeyboardButton("📥 تحميل فيديو", callback_data=f"video|{url}")],
        [InlineKeyboardButton("🎵 تحميل صوت MP3", callback_data=f"audio|{url}")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("اختر نوع التحميل:", reply_markup=reply_markup)

# --- الضغط على الأزرار ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, url = query.data.split("|")

    await query.edit_message_text("⏳ جاري التحميل...")

    try:
        if action == "video":
            file = download_video(url)
            await context.bot.send_video(
                chat_id=query.message.chat.id,
                video=open(file, "rb")
            )

        elif action == "audio":
            file = download_audio(url)
            await context.bot.send_audio(
                chat_id=query.message.chat.id,
                audio=open(file, "rb")
            )

        os.remove(file)

    except Exception as e:
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=f"❌ فشل التحميل\nخطأ: {str(e)}"
        )

# --- تشغيل البوت مباشرة بدون asyncio.run() ---
if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot Started...")
    app.run_polling()  # <-- هنا نبدأ البوت مباشرة بدون asyncio.run()
