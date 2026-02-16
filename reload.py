import subprocess
import time
import os
import sys
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Files to watch (absolute paths)
WATCHED_FILES = [
    BASE_DIR / "gmail_notifier.py",
    BASE_DIR / "config.py",
    BASE_DIR / ".env"
]

def get_mtimes():
    """Get modification times of watched files"""
    mtimes = {}
    for f in WATCHED_FILES:
        try:
            if f.exists():
                mtimes[str(f)] = f.stat().st_mtime
        except Exception:
            pass
    return mtimes

def main():
    print(f"🚀 Gmail Notifier Reloader started.")
    print(f"👀 Watching: {[f.name for f in WATCHED_FILES]}")
    
    notifier_script = str(BASE_DIR / "gmail_notifier.py")
    
    process = None
    
    try:
        # Initial start
        process = subprocess.Popen([sys.executable, notifier_script])
        last_mtimes = get_mtimes()
        
        while True:
            time.sleep(2)  # Check every 2 seconds
            
            # Check if files changed
            current_mtimes = get_mtimes()
            if current_mtimes != last_mtimes:
                print("\n🔄 Changes detected in configuration or script. Restarting...")
                if process:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                
                process = subprocess.Popen([sys.executable, notifier_script])
                last_mtimes = current_mtimes
                print("✅ Restarted successfully.")
            
            # If the process died unexpectedly, restart it
            if process.poll() is not None:
                print(f"\n⚠️ Notifier process died with exit code {process.returncode}. Restarting in 5 seconds...")
                time.sleep(5)
                process = subprocess.Popen([sys.executable, notifier_script])
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping Gmail Notifier Reloader...")
        if process:
            process.terminate()
            process.wait()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error in reloader: {e}")
        if process:
            process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()
