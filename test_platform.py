import platform
import os
import subprocess
import time
from pathlib import Path

# Mock config-like behavior
BASE_DIR = Path(__file__).resolve().parent
SOUND_PATH = BASE_DIR / "notify.wav"
SOUND_ENABLED = True

def log(msg):
    print(f"[*] {msg}")

def test_os_detection():
    os_name = platform.system()
    log(f"Detected Operating System: {os_name}")
    log(f"Platform Detail: {platform.platform()}")
    return os_name

def test_sound_logic(os_name):
    log(f"Testing sound logic for {os_name}...")
    if not os.path.exists(SOUND_PATH):
        print(f"[!] Warning: {SOUND_PATH} not found. Sound test might fail.")
    
    # We display what command WOULD be run
    if os_name == "Linux":
        log("Command 1: paplay notify.wav")
        log("Command 2 (fallback): aplay notify.wav")
    elif os_name == "Darwin":
        log("Command: afplay notify.wav")
    elif os_name == "Windows":
        log("Command: PowerShell (New-Object Media.SoundPlayer 'notify.wav').PlaySync()")
    
    log("Running sound player now (capped at 1s)...")
    try:
        proc = None
        if os_name == "Linux":
            try: proc = subprocess.Popen(["paplay", str(SOUND_PATH)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except: proc = subprocess.Popen(["aplay", str(SOUND_PATH)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif os_name == "Darwin":
            proc = subprocess.Popen(["afplay", str(SOUND_PATH)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif os_name == "Windows":
            cmd = f"PowerShell -c (New-Object Media.SoundPlayer '{str(SOUND_PATH)}').PlaySync();"
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if proc:
            time.sleep(1)
            proc.terminate()
            log("Sound command executed successfully.")
    except Exception as e:
        log(f"Sound test failed: {e}")

def test_notification():
    log("Testing notification system (via plyer)...")
    try:
        from plyer import notification
        notification.notify(
            title="Platform Test",
            message="If you see this, notifications are working on your OS!",
            app_name="Gmail Notifier Test",
            timeout=5
        )
        log("Notification request sent.")
    except ImportError:
        log("Error: 'plyer' not installed. Run 'pip install plyer'")
    except Exception as e:
        log(f"Notification failed: {e}")

if __name__ == "__main__":
    current_os = test_os_detection()
    print("-" * 30)
    test_sound_logic(current_os)
    print("-" * 30)
    test_notification()
    print("-" * 30)
    log("Test complete. If you heard a 'ding' and saw a popup, this OS is supported!")
