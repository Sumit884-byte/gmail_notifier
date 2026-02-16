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


def notify_user(title, message, timeout=10, icon=None, play_sound=False, url=None):
    """Unified notification helper with Linux fallback and optional sound/clickable URL"""
    app_icon = icon if icon and os.path.exists(icon) else None
    
    if play_sound:
        play_notification_sound()

    # If it's Linux and we have a URL, use notify-send for interactivity
    if platform.system() == "Linux" and url:
        try:
            # We use --action to make it clickable
            # --wait is required for --action to capture the response
            cmd = ["notify-send", "--app-name=Gmail Notifier", "--wait", "--action=default=Open Gmail", title, message]
            if app_icon:
                cmd.extend(["-i", app_icon])
            
            # Run in background so it doesn't block the main loop
            # But we need to handle the output to know if it was clicked
            def run_and_open():
                result = subprocess.run(cmd, capture_output=True, text=True)
                if "default" in result.stdout:
                    subprocess.run(["xdg-open", url])
            
            import threading
            threading.Thread(target=run_and_open, daemon=True).start()
            return
        except Exception as e:
            log_to_file(f"⚠️ Interactive notify-send failed: {e}")

    # Fallback to standard plyer notification (non-interactive)
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
        # Standard fallback for Linux
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


import json

def read_counts():
    """Read all counts from JSON file"""
    if os.path.exists(config.STATE_FILE):
        try:
            with open(config.STATE_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except:
            pass
    return {}


def write_counts(counts):
    """Write all counts to JSON file"""
    with open(config.STATE_FILE, "w") as f:
        json.dump(counts, f, indent=2)


def get_last_count(email):
    counts = read_counts()
    return counts.get(email, -1)


def set_last_count(email, count):
    counts = read_counts()
    counts[email] = count
    write_counts(counts)


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


def get_unread_emails(username, password):
    """Returns tuple: (count, list of email dicts with subject, author, summary)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(config.ATOM_FEED, auth=HTTPBasicAuth(username, password), headers=headers)
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
                link_elem = entry.find('atom:link', ns)

                email_data = {
                    'subject': title_elem.text if title_elem is not None else 'No Subject',
                    'author': author_elem.text if author_elem is not None else 'Unknown',
                    'summary': strip_html_tags(summary_elem.text) if summary_elem is not None else '',
                    'link': link_elem.get('href') if link_elem is not None else None
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
start_message = f"Gmail Notifier started for {len(config.ACCOUNTS)} accounts"
log_to_file(start_message)
notify_user("Service Started", start_message, icon=config.ICON_PATH, url=config.GMAIL_URL)

while True:
    for account in config.ACCOUNTS:
        email_addr = account['email']
        password = account['password']
        
        last_count = get_last_count(email_addr)
        current_count, emails = get_unread_emails(email_addr, password)

        if current_count == -1:
            continue

        if current_count != last_count:
            log_to_file(f"[{email_addr}] Unread count changed: {last_count} ➝ {current_count}")
            set_last_count(email_addr, current_count)

            if current_count > last_count:
                # New message(s) arrived
                new_messages_count = current_count - last_count
                if last_count == -1: # First run for this account
                    new_messages_count = 0 # Don't notify for old emails on first run

                # Show detailed notification for each new email
                for i, email in enumerate(emails[:new_messages_count]):
                    subject = email['subject']
                    author = email['author']
                    summary = email['summary']

                    # Truncate summary if too long
                    if len(summary) > config.MAX_CONTENT_LENGTH:
                        summary = summary[:config.MAX_CONTENT_LENGTH] + "..."

                    title = f"New Email ({email_addr})"
                    message = f"From: {author}\nSubject: {subject}\n\n{summary}"
                    
                    # Use specific email link if available, fallback to inbox
                    email_url = email.get('link') or config.GMAIL_URL
                    
                    notify_user(title, message, timeout=10, icon=config.ICON_PATH, play_sound=True, url=email_url)
                    log_to_file(f"[{email_addr}] Notified: '{subject}' from {author}")

                    if i < new_messages_count - 1:
                        time.sleep(1)

    time.sleep(config.CHECK_INTERVAL)