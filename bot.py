# bot.py
import asyncio
import logging
import os
import time
from pathlib import Path
from functools import wraps

from config import BOT_TOKEN, DOWNLOADS_DIR, USER_RATE_LIMIT_PER_HOUR, MAX_CONCURRENT_DOWNLOADS, ADMINS, DEFAULT_LANG
from downloader import download_media, DownloadResult

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("social-downloader-bot")

# Simple in-memory rate limiting and concurrency
user_requests = {}
active_downloads = 0
download_lock = asyncio.Lock()

def rate_limited(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *a, **kw):
        user_id = update.effective_user.id
        now = int(time.time())
        window = 3600
        user_times = user_requests.get(user_id, [])
        # remove old
        user_times = [t for t in user_times if t > now - window]
        if len(user_times) >= USER_RATE_LIMIT_PER_HOUR and user_id not in ADMINS:
            await update.message.reply_text("تجاوزت حد الطلبات في الساعة. حاول لاحقاً.")
            return
        user_times.append(now)
        user_requests[user_id] = user_times
        return await func(update, context, *a, **kw)
    return wrapper

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "مرحباً! أنا بوت تنزيل احترافي. أرسل رابط أي ميديا أو استخدم /help لمعرفة الأوامر."
    await update.message.reply_text(txt)

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        "أوامر متاحة:\n"
        "/start - بداية\n"
        "/help - المساعدة\n"
        "/settings - إعداداتك (مستخدم)\n"
        "/about - معلومات عن البوت\n\n"
        "أرسل رابط (YouTube/TikTok/Instagram/...) وسيبدأ التحميل.\n"
        "يمكنك أيضاً استخدام أوامر متقدمة لاحقاً."
    )
    await update.message.reply_text(txt)

@rate_limited
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_downloads
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("أرسل رابط أو نص صالح للبحث.")
        return
    # detect if it's a search query or link
    is_url = any(text.startswith(s) for s in ("http://", "https://", "www.", "youtu", "tiktok", "instagram", "facebook", "twitter", "x.com", "reddit"))
    if not is_url:
        # treat as ytsearch
        query = f"ytsearch:{text}"
    else:
        query = text

    # concurrency limit
    if active_downloads >= MAX_CONCURRENT_DOWNLOADS:
        await update.message.reply_text("يوجد تنزيلات جارية حالياً. حاول بعد قليل.")
        return

    # start download
    msg = await update.message.reply_text("جارٍ التحضير للتحميل...")

    async with download_lock:
        active_downloads += 1
    try:
        # prefer format selection UI: provide basic choices
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Video (best)", callback_data=f"dl|{query}|best")],
            [InlineKeyboardButton("Audio (mp3)", callback_data=f"dl|{query}|audio")],
            [InlineKeyboardButton("Cancel", callback_data="cancel")]
        ])
        await msg.edit_text("اختر نوع التحميل:", reply_markup=keyboard)
    finally:
        async with download_lock:
            active_downloads -= 1

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_downloads
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "cancel":
        await query.edit_message_text("تم الإلغاء.")
        return
    if not data.startswith("dl|"):
        await query.edit_message_text("بيانات غير معروفة.")
        return
    _, raw_query, mode = data.split("|", 2)
    # start actual download
    # increment active downloads safely
    async with download_lock:
        if active_downloads >= MAX_CONCURRENT_DOWNLOADS:
            await query.edit_message_text("تحميلات كثيرة حالياً. حاول لاحقاً.")
            return
        active_downloads += 1
    try:
        m = await query.edit_message_text("بدء التنزيل، الرجاء الانتظار...")
        extract_audio = (mode == "audio")
        format_selector = None
        if mode == "best":
            format_selector = "bestvideo+bestaudio/best"
        res = await download_media(raw_query, format_selector=format_selector, extract_audio=extract_audio)
        fp = res.filepath
        # if file too large
        if res.meta.get("warning") == "file_too_large" or fp.stat().st_size > int(os.getenv("MAX_FILE_SIZE_BYTES", 150*1024*1024)):
            await m.edit_text("الملف الناتج كبير جداً. أرسِلته للرفع السحابي (لمفعل) أو استخدم رابط مباشر.")
            # For now, just inform user and provide local path (in production: upload to drive)
            await query.message.reply_text(f"الملف جاهز على الخادم: {fp}")
        else:
            # send file
            await m.edit_text("جارٍ رفع الملف إلى Telegram...")
            await query.message.reply_document(document=InputFile(fp), filename=fp.name)
            await m.edit_text("تم الرفع بنجاح.")
    except Exception as e:
        logger.exception("Download failed")
        await query.edit_message_text(f"فشل التحميل: {e}")
    finally:
        async with download_lock:
            active_downloads -= 1
        # cleanup: you may schedule deletion by background job

async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("social-downloader-bot — بوت تنزيل احترافي متعدد المنصات.\nصنع بواسطة فريق التطوير.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("about", about_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    print("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
