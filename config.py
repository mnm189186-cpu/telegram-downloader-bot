# config.py
import os
from pathlib import Path

# Telegram
BOT_TOKEN = os.getenv("8727487234:AAFxv4TwkBjflhPOSy1qHicoMsNVeWJ8bEw", "REPLACE_WITH_YOUR_BOT_TOKEN")

# Optional YouTube API Key (for Data API search). If empty, yt-dlp search used.
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# Paths
BASE_DIR = Path(__file__).parent.resolve()
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Limits & settings
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_BYTES", 150 * 1024 * 1024))  # default 150MB
USER_RATE_LIMIT_PER_HOUR = int(os.getenv("USER_RATE_LIMIT_PER_HOUR", 30))
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", 3))

# yt-dlp & ffmpeg
YTDLP_BINARY = os.getenv("YTDLP_BINARY", "yt-dlp")
FFMPEG_BINARY = os.getenv("FFMPEG_BINARY", "ffmpeg")

# Storage options
USE_GOOGLE_DRIVE = os.getenv("USE_GOOGLE_DRIVE", "false").lower() == "true"
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

# Admins (Telegram user IDs comma separated)
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x.strip().isdigit()]

# Language
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "ar")  # "ar" or "en"

# Misc
TEMP_FILE_TTL_SECONDS = int(os.getenv("TEMP_FILE_TTL_SECONDS", 60 * 60 * 24))  # 24h
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
