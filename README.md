# Gmail Notifier

A desktop notification service for unread Gmail messages.

## Features
- **Multi-Account Support**: Monitor multiple Gmail accounts simultaneously.
- **Interactive Notifications**: Click the notification to open the specific email in your browser.
- **Auto-Reloader**: Dynamically restarts the service when you update your settings or code.
- **High-quality sound notifications**: Includes a premium "Chime" sound (`notify.wav`) for clear alerts.
- **Detailed information**: Subject and summary snippet.
- **Logging of changes**.

## 🌍 Cross-Platform Compatibility
This project is designed to be universal and runs seamlessly on **Linux, Windows, and macOS**.
- **Notifications**: Uses native system popups on all platforms (Toast on Windows, Notification Center on macOS, and Libnotify/DBus on Linux).
- **Sound**: Automatically detects your OS and uses the native audio player (`paplay`/`aplay` on Linux, `afplay` on macOS, and `PowerShell` on Windows) to play alerts.
- **Paths**: Uses dynamic path resolution so the script works regardless of where the project folder is placed.

## Setup
1. Clone the repository.
2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   # On Linux/macOS:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate

   pip install -r requirements.txt
   ```
3. Configure your credentials in `.env` (create this file from the template if needed):
   ```env
   GMAIL_USERNAME=your_email@gmail.com
   GMAIL_PASSWORD=your_app_password

   # OPTIONAL: Monitor multiple accounts
   # Format: email1:pass1,email2:pass2
   GMAIL_ACCOUNTS=other_user@gmail.com:pass123,another_user@gmail.com:pass456
   ```

### 🔑 How to get a Gmail App Password
Standard passwords will not work. You must generate a 16-character **App Password**:
1. Go to your [Google Account Settings](https://myaccount.google.com/).
2. Navigate to the **Security** tab.
3. Ensure **2-Step Verification** is turned **ON**.
4. In the search bar at the top, type **"App Passwords"** and select it.
5. Enter a name for the app (e.g., `Desktop Notifier`).
6. Click **Create**.
7. Copy the generated **16-character password** (e.g., `abcd efgh ijkl mnop`).
8. Paste this code into the `GMAIL_PASSWORD` field in your `.env` file (remove any spaces).

## Usage
### Standard Mode
Run the script directly:
```bash
python gmail_notifier.py
```

### Development Mode (Auto-Reload)
If you are changing settings or code, use the reloader to automatically restart upon changes:
```bash
python reload.py
```

## Files
- `gmail_notifier.py`: The main script (now cross-platform).
- `config.py`: Centralized configuration with dynamic path detection.
- `.env`: Contains sensitive credentials (ignored by git).
- `requirements.txt`: Python dependencies (including `plyer` for notifications).
- `gmail_check.log`: Log file (located in the script folder).
- `last_count.txt`: Stores state (located in the script folder).

## Automatic Startup & Persistence

The project includes an **automatic setup script** that configures the notifier to start when you log in, tailored to your operating system.

### One-Click Setup
After configuring your `.env` file and creating the virtual environment, simply run:
```bash
python setup_startup.py
```

**What it does:**
- **Linux**: Creates and enables a `systemd` user service.
- **Windows**: Creates a startup batch file in your `AppData\...\Startup` folder.
- **macOS**: Creates and loads a `LaunchAgent` `.plist` file.

### Manual Setup (Optional)
If you prefer to do it manually, you can find the detailed instructions below for your OS:

<details>
<summary>Linux (Systemd)</summary>

1. Create the service file:
   ```bash
   mkdir -p ~/.config/systemd/user/
   nano ~/.config/systemd/user/gmail-notifier.service
   ```
2. Paste the configuration (update paths):
   ```ini
   [Unit]
   Description=Gmail Notifier Service
   [Service]
   ExecStart=/path/to/venv/bin/python /path/to/gmail_notifier.py
   Restart=always
   [Install]
   WantedBy=default.target
   ```
3. Run: `systemctl --user enable --now gmail-notifier.service`
</details>

<details>
<summary>Windows (Startup Folder)</summary>

1. Create a shortcut to `pythonw.exe` from your `venv\Scripts`.
2. Move it to `shell:startup`.
</details>

<details>
<summary>macOS (Launch Agents)</summary>

1. Create a `.plist` in `~/Library/LaunchAgents/`.
2. Use `launchctl load` to start it.
</details>

---

---

### Alternative: Using Crontab (Linux/macOS)
1. Open crontab: `crontab -e`
2. Add this line:
   ```bash
   @reboot cd /path/to/your/project && /path/to/your/project/venv/bin/python gmail_notifier.py
   ```

## 📡 About Gmail Atom Feed

This project uses the **Gmail Atom Feed** (`https://mail.google.com/mail/feed/atom`) to fetch unread emails. Here’s why it’s useful and how it can be used:

### Why use the Atom Feed?
- **Lightweight**: It returns basic XML data, making it much faster and less resource-intensive than the full Gmail API.
- **Minimal Setup**: You don't need to register an app in the Google Cloud Console or manage complex OAuth2 tokens.
- **Real-time-ish**: It provides a quick way to poll for updates without heavy overhead.

### Various Use Cases
1. **Status Bar Indicators**: Integrate the feed count into terminal-based status bars like `i3status`, `Polybar`, or `Waybar` to see unread counts at a glance.
2. **IoT Notifications**: Use a Raspberry Pi or ESP32 with an LED (e.g., "The Mail Light") that glows when the Atom feed count is greater than zero.
3. **Command Line Tools**: Create a simple alias in your `.bashrc` or `.zshrc` to quickly list recent unread email subjects without opening a browser.
4. **Minimalist Workflows**: Perfect for "distraction-free" environments where you want to know if a message arrived without being sucked into the full Gmail interface.
5. **Server Health/Alerts**: Monitor a specific Gmail account dedicated to server alerts or log notifications using a simple cron job.

### Accessing Labels and Categories
Did you know you can filter the feed? By default, it shows the **Inbox**, but you can target specific labels or Google categories:
- **Promotions**: `https://mail.google.com/mail/feed/atom/category-promotions`
- **Updates**: `https://mail.google.com/mail/feed/atom/category-updates`
- **Social**: `https://mail.google.com/mail/feed/atom/category-social`
- **Custom Labels**: `https://mail.google.com/mail/feed/atom/your-label-name`

To use these in the script, simply update the `ATOM_FEED` variable in `config.py` or your `.env` file.

### Limitations
- Only reflects emails currently in the targeted label.
- Does not support complex filtering or searching (use the full Gmail API for that).
- Requires Basic Auth (via App Passwords), which must be handled securely.

## ⏳ Rate Limits & Polling
Google does not publish a strict "hard limit" for the Atom feed, but it is highly sensitive to aggressive polling.

- **Current Default**: The script is set to poll every **1 second** (for testing purposes).
- **Recommended**: For production or daily use, set `CHECK_INTERVAL` to **60 seconds** or higher.
- **Risks of Fast Polling**:
    - **Temporary Bans**: Your IP or account may be temporarily blocked from the feed.
    - **401/403 Errors**: Google may start rejecting valid credentials if requested too frequently.
    - **Battery/Data Drain**: Constant polling is inefficient for laptops and mobile data.

To change the interval, edit the `CHECK_INTERVAL` in `config.py` or add this to your `.env`:
```env
CHECK_INTERVAL=60
SOUND_ENABLED=true
SOUND_PATH=/home/s/code/py/main/notify.wav
```
