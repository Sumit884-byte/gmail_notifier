import os
import re
import html
import time
import requests
import subprocess
import platform
import warnings
import xml.etree.ElementTree as ET
from datetime import datetime
from requests.auth import HTTPBasicAuth

# Suppress plyer/dbus warnings
warnings.filterwarnings("ignore", category=UserWarning, module="plyer.platforms.linux.notification")

from plyer import notification
import config

# === HELPERS ===

def play_notification_sound():
    """Play a notification sound and stop after 1 sec as requested"""
    if not config.SOUND_ENABLED or not os.path.exists(config.SOUND_PATH):
        return

    try:
        proc = None
        if platform.system() == "Linux":
            # Try paplay then aplay
            try:
                proc = subprocess.Popen(["paplay", config.SOUND_PATH], 
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                proc = subprocess.Popen(["aplay", config.SOUND_PATH], 
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif platform.system() == "Darwin":  # macOS
            proc = subprocess.Popen(["afplay", config.SOUND_PATH], 
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif platform.system() == "Windows":
            cmd = f"PowerShell -c (New-Object Media.SoundPlayer '{config.SOUND_PATH}').PlaySync();"
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if proc:
            # Wait for 1 second then terminate if still running
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.terminate()
    except Exception as e:
        log_to_file(f"⚠️ Failed to play sound: {e}")


def notify_user(title, message, timeout=10, icon=None, play_sound=False):
    """Unified notification helper with Linux fallback and optional sound"""
    app_icon = icon if icon and os.path.exists(icon) else None
    
    if play_sound:
        play_notification_sound()

    # Try plyer first
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Gmail Notifier",
            app_icon=app_icon,
            timeout=timeout
        )
    except Exception as e:
        log_to_file(f"⚠️ Plyer notification failed: {e}")
        # Fallback for Linux
        if platform.system() == "Linux":
            try:
                cmd = ["notify-send", title, message]
                if app_icon:
                    cmd.extend(["-i", app_icon])
                subprocess.run(cmd)
            except Exception as e2:
                log_to_file(f"❌ Linux fallback notification failed: {e2}")

def log_to_file(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(config.LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def read_last_count():
    if os.path.exists(config.STATE_FILE):
        try:
            with open(config.STATE_FILE, "r") as f:
                return int(f.read().strip())
        except:
            pass
    return -1


def write_last_count(count):
    with open(config.STATE_FILE, "w") as f:
        f.write(str(count))


def strip_html_tags(text):
    """Remove HTML tags and decode HTML entities"""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub('<.*?>', '', text)
    # Decode HTML entities
    clean = html.unescape(clean)
    # Remove extra whitespace
    clean = ' '.join(clean.split())
    return clean


def get_unread_emails():
    """Returns tuple: (count, list of email dicts with subject, author, summary)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(config.ATOM_FEED, auth=HTTPBasicAuth(config.USERNAME, config.PASSWORD), headers=headers)
        if response.status_code == 200:
            # Parse XML
            root = ET.fromstring(response.text)

            # Define namespace
            ns = {'atom': 'http://purl.org/atom/ns#'}

            # Get fullcount
            fullcount_elem = root.find('atom:fullcount', ns)
            count = int(fullcount_elem.text) if fullcount_elem is not None else 0

            # Get email entries
            emails = []
            for entry in root.findall('atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                author_elem = entry.find('atom:author/atom:name', ns)
                summary_elem = entry.find('atom:summary', ns)

                email_data = {
                    'subject': title_elem.text if title_elem is not None else 'No Subject',
                    'author': author_elem.text if author_elem is not None else 'Unknown',
                    'summary': strip_html_tags(summary_elem.text) if summary_elem is not None else ''
                }
                emails.append(email_data)

            return count, emails
        else:
            log_to_file(f"❌ HTTP Error {response.status_code}")
    except Exception as e:
        log_to_file(f"❌ Exception: {str(e)}")
    return -1, []


# === MAIN LOOP ===

# Log and notify that the script has started
start_message = f"Gmail Notifier started for {config.USERNAME}"
log_to_file(start_message)
notify_user("Service Started", start_message, timeout=3, icon=config.ICON_PATH)

last_count = read_last_count()

while True:
    current_count, emails = get_unread_emails()

    if current_count == -1:
        time.sleep(config.CHECK_INTERVAL)
        continue

    if current_count != last_count:
        log_to_file(f"Unread count changed: {last_count} ➝ {current_count}")
        write_last_count(current_count)

        if current_count > last_count:
            # New message(s) arrived
            # Determine how many new emails to show (prevent index errors)
            new_messages_count = current_count - last_count

            # Show detailed notification for each new email
            for i, email in enumerate(emails[:new_messages_count]):
                subject = email['subject']
                author = email['author']
                summary = email['summary']

                # Truncate summary if too long
                if len(summary) > config.MAX_CONTENT_LENGTH:
                    summary = summary[:config.MAX_CONTENT_LENGTH] + "..."

                title = f"New Email from {author}"
                message = f"Subject: {subject}\n\n{summary}"

                notify_user(title, message, timeout=10, icon=config.ICON_PATH, play_sound=True)

                log_to_file(f"Notified: '{subject}' from {author}")

                # Small delay between notifications if multiple emails
                if i < new_messages_count - 1:
                    time.sleep(1)

            # The xdg-open line has been removed to prevent the browser from opening.

        last_count = current_count

    time.sleep(config.CHECK_INTERVAL)