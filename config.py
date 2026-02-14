import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the script
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

# === CREDENTIALS ===
# USERNAME = os.getenv("GMAIL_USERNAME", "sah299610@gmail.com")
USERNAME = os.getenv("GMAIL_USERNAME")

PASSWORD = os.getenv("GMAIL_PASSWORD")

# === URLS ===
ATOM_FEED = os.getenv("GMAIL_ATOM_FEED", "https://mail.google.com/mail/feed/atom")
GMAIL_URL = "https://mail.google.com"

# === SETTINGS ===
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))  # seconds
ICON_PATH = "/usr/share/icons/Adwaita/32x32/status/mail-unread.png"
LOG_FILE = BASE_DIR / "gmail_check.log"
STATE_FILE = BASE_DIR / "last_count.txt"
MAX_CONTENT_LENGTH = 100  # Max characters to show in notification

# === SOUND ===
SOUND_ENABLED = os.getenv("SOUND_ENABLED", "true").lower() == "true"
SOUND_PATH = os.getenv("SOUND_PATH", str(BASE_DIR / "notify.wav"))
