import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the script
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

# === CREDENTIALS ===
ACCOUNTS = []

# Single account for backward compatibility
if os.getenv("GMAIL_USERNAME") and os.getenv("GMAIL_PASSWORD"):
    ACCOUNTS.append({
        "email": os.getenv("GMAIL_USERNAME"),
        "password": os.getenv("GMAIL_PASSWORD")
    })

# Multiple accounts from environment variable
# Format 1: email1:pass1,email2:pass2
extra_accounts = os.getenv("GMAIL_ACCOUNTS", "")
if extra_accounts:
    for pair in extra_accounts.split(","):
        if ":" in pair:
            email, password = pair.split(":", 1)
            ACCOUNTS.append({"email": email.strip(), "password": password.strip()})

# Format 2 (JSON): [{"email": "...", "password": "..."}, ...]
accounts_json = os.getenv("GMAIL_ACCOUNTS_JSON", "")
if accounts_json:
    try:
        import json
        JSON_ACCOUNTS = json.loads(accounts_json)
        if isinstance(JSON_ACCOUNTS, list):
            ACCOUNTS.extend(JSON_ACCOUNTS)
    except Exception:
        pass

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
