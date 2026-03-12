import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from config import TOKEN
from downloader import download_media


# رسالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("📥 تحميل من رابط", callback_data="download")],
        [InlineKeyboardButton("ℹ️ مساعدة", callback_data="help")]
    ]

    await update.message.reply_text(
        "🤖 بوت تحميل وسائل التواصل\n\n"
        "ارسل رابط من:\n"
        "YouTube\nTikTok\nInstagram\nFacebook\nTwitter\n\n"
        "وسيتم تحميله مباشرة.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# الأزرار
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "download":
        await query.edit_message_text("📩 أرسل الرابط الآن")

    elif query.data == "help":
        await query.edit_message_text(
            "📌 طريقة الاستخدام:\n\n"
            "1- اضغط تحميل\n"
            "2- أرسل رابط الفيديو\n"
            "3- سيقوم البوت بتنزيله"
        )


# استقبال الروابط
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = update.message.text

    await update.message.reply_text("⏳ جاري التحميل...")

    try:

        file = download_media(url)

        await update.message.reply_video(
            video=open(file, "rb")
        )

        os.remove(file)

    except Exception as e:

        await update.message.reply_text("❌ فشل التحميل")


def main():

    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
