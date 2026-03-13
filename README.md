# social-downloader-bot

بوت Telegram بسيط لتنزيل الفيديو والصوت باستخدام yt-dlp وffmpeg.

ملف الإعدادات: انسخ `.env.example` إلى `.env` وعبّئ القيم (BOT_TOKEN إلخ).

تشغيل محلي:
1. python -m venv .venv
2. source .venv/bin/activate
3. pip install --upgrade pip
4. pip install -r requirements.txt
5. تأكد أن ffmpeg مثبت:
   sudo apt update && sudo apt install -y ffmpeg
6. قم بضبط متغير BOT_TOKEN في .env ثم:
   python bot.py

Docker:
- docker build -t social-downloader-bot .
- docker run --env-file .env -v ./downloads:/app/downloads social-downloader-bot
