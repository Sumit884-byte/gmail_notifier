import os
import sys
import platform
import subprocess
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = BASE_DIR / "gmail_notifier.py"
VENV_PYTHON = BASE_DIR / "venv" / ("bin" if platform.system() != "Windows" else "Scripts") / ("python" if platform.system() != "Windows" else "python.exe")

def setup_linux():
    print("[*] Setting up persistence for Linux (Systemd)...")
    service_content = f"""[Unit]
Description=Gmail Notifier Service
After=network.target

[Service]
ExecStart={VENV_PYTHON} {SCRIPT_PATH}
WorkingDirectory={BASE_DIR}
Restart=always
Environment=DISPLAY=:0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{os.getuid()}/bus

[Install]
WantedBy=default.target
"""
    service_path = Path.home() / ".config" / "systemd" / "user" / "gmail-notifier.service"
    service_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(service_path, "w") as f:
        f.write(service_content)
    
    subprocess.run(["systemctl", "--user", "daemon-reload"])
    subprocess.run(["systemctl", "--user", "enable", "gmail-notifier.service"])
    subprocess.run(["systemctl", "--user", "start", "gmail-notifier.service"])
    print(f"[+] Service created and started at: {service_path}")
    print("[!] Done! Use 'systemctl --user status gmail-notifier.service' to check status.")

def setup_windows():
    print("[*] Setting up persistence for Windows (Startup Folder)...")
    startup_folder = Path(os.getenv("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    shortcut_path = startup_folder / "GmailNotifier.bat"
    
    # Use pythonw.exe to run without a console window if possible
    PYTHONW = VENV_PYTHON.parent / "pythonw.exe"
    EXE = PYTHONW if PYTHONW.exists() else VENV_PYTHON

    content = f'@echo off\nstart "" "{EXE}" "{SCRIPT_PATH}"'
    
    with open(shortcut_path, "w") as f:
        f.write(content)
        
    print(f"[+] Startup batch file created at: {shortcut_path}")
    print("[!] Done! The script will now run automatically on login.")

def setup_macos():
    print("[*] Setting up persistence for macOS (Launch Agents)...")
    plist_label = "com.user.gmailnotifier"
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"{plist_label}.plist"
    
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{plist_label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{VENV_PYTHON}</string>
        <string>{SCRIPT_PATH}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{BASE_DIR}</string>
</dict>
</plist>
"""
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(plist_path, "w") as f:
        f.write(plist_content)
    
    subprocess.run(["launchctl", "load", str(plist_path)])
    print(f"[+] LaunchAgent created and loaded at: {plist_path}")
    print("[!] Done!")

def main():
    if not SCRIPT_PATH.exists():
        print(f"[!] Error: {SCRIPT_PATH} not found!")
        return

    if not VENV_PYTHON.exists():
        print(f"[!] Error: Virtual environment not found at {VENV_PYTHON.parent}!")
        print("[!] Please create it first using 'python3 -m venv venv'")
        return

    os_type = platform.system()
    if os_type == "Linux":
        setup_linux()
    elif os_type == "Windows":
        setup_windows()
    elif os_type == "Darwin":
        setup_macos()
    else:
        print(f"[!] Unsupported OS: {os_type}")

if __name__ == "__main__":
    main()
