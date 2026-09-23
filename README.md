# Telegram Anti-NSFW & Heart Emoji Shield Bot 🛡️

> 🚀 **Looking for the Serverless edition?**  
> Run this bot without a VPS or servers using Telegram's official infrastructure:  
> 👉 **[NotMmd/antinsfwbot-serverless](https://github.com/NotMmd/antinsfwbot-serverless)**

---

An advanced, automated Telegram moderation bot written in Python (`python-telegram-bot` v22+) that detects single heart/suggestive emoji spam posted under newly published channel posts within a customizable time window (default 30 minutes).

When detected, the bot applies the configured moderation settings, then sends an alert with interactive action buttons (**Ban Group**, **Ban Channel**, **Ban Both**, **Unmute**, **Keep Muted**) to admins' private chats.

---

## 🎯 Why This Bot Exists

Automated NSFW bot accounts frequently target Telegram channel discussion groups by posting single heart/mouth emojis (`❤️`, `💗`, `❤️‍🔥`, `🫦`, `👄`) under newly published channel posts within minutes of release. 

These userbots aim to stay top-of-comment so group members click their profile pictures/bios, leading to NSFW promotion channels or malware distribution.

This bot intercepts and eliminates this spam pattern by:
1. Learning channel post timestamps and discussion thread roots automatically.
2. Tracking new member join service messages so they can be deleted upon ban.
3. Automatically muting or banning the user and optionally purging the comment when sent within the configured window.
4. Sending an interactive dashboard directly to the admin with instant 1-click confirmation flows.

---

## ✨ Features

- 🎯 **Targeted Spam & Emoji Normalization:** Filters messages containing ONLY a single heart or suggestive emoji (`🩷❤️🧡💛💚🩵💙💜🖤🩶🤍🤎❤️‍🔥❤️‍🩹❣️💕💞💓💗💖💘💝🫦👄`). Cleans Unicode variation selectors (VS15/VS16, ZWJ, BOM) so hidden zero-width bypasses fail.
- ⏱️ **Configurable Detection Window:** Set via `WINDOW_MINUTES` in `.env` (defaults to 30 minutes).
- 🗄️ **Smart SQLite Storage:** Tracks channel posts, auto-forwarded discussion thread IDs, and member join message IDs across bot restarts.
- 🧹 **Auto Clean Join Messages:** Deletes the user's initial `"User joined the group"` message when banned to keep the chat spotless.
- 🚨 **Admin DM Control Panel:** Forwards the offending message to the admin's DM with interactive confirmation buttons:
  - 🚷 **Ban Group:** Bans from discussion group & deletes join message.
  - 🚫 **Ban Channel:** Bans from the main channel.
  - 🔨 **Ban Both:** Complete purge from both channel and discussion group.
  - 🔊 **Unmute:** Restores user permissions.
  - ❌ **Keep Muted:** Keeps the user restricted.
- 🛡️ **Permission Health Check:** Automatically tests group & channel admin rights on startup and alerts the admin if rights (like `can_restrict_members` or `can_delete_messages`) are missing, with an interactive retry button.
- ⚙️ **Live Moderation Settings:** Admins can use `/settings` or `/panel` in a private chat to toggle auto-ban, auto-delete, and admin alerts, and choose whether automatic bans apply to the group, channel, or both. Settings persist in SQLite and take effect on the next detected message.

---

## 🚀 Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/NotMmd/antinsfwbot.git
cd antinsfwbot
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
nano .env
```

Fill in your configuration:
```ini
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TARGET_GROUP_ID=-1001234567890
TARGET_CHANNEL_ID=-1001234567891
ADMIN_DM_ID=123456789
ADMIN_IDS=123456789
WINDOW_MINUTES=30
DB_PATH=posts.db
AUTO_BAN=false
AUTO_DELETE=true
BAN_SCOPE=group
NOTIFY_ADMIN=true
```

`ADMIN_IDS` accepts a comma-separated list of admin Telegram user IDs. If omitted, `ADMIN_DM_ID` is used for admin authorization and alerts. The four moderation variables provide defaults; values saved from the inline settings panel are stored in SQLite and override those defaults for this configured group/channel pair. When auto-ban is off, detected users are muted as before. The selected scope controls auto-ban destinations; users not banned from the group remain muted there.

In a private chat with the bot, send `/settings` or `/panel` to change the live settings.

---

## ⚙️ Running the Bot

### Option 1: Direct Execution
```bash
python main.py
```

### Option 2: Systemd Service (Production)
Create `/etc/systemd/system/antinsfwbot.service`:
```ini
[Unit]
Description=Anti-NSFW Heart Emoji Telegram Bot
After=network.target

[Service]
Type=simple
User=mamad
WorkingDirectory=/path/to/antinsfwbot
ExecStart=/path/to/antinsfwbot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now antinsfwbot
```

---

## 🔒 Required Admin Permissions

Make sure the bot has admin privileges:
- **In Discussion Group:**
  - ✅ `Delete Messages`
  - ✅ `Restrict Members`
- **In Channel:**
  - ✅ `Administrator` (with user restrict / post permissions)

---

## 📜 License

Distributed under the [MIT License](LICENSE).

---
<sub>⚡ Vibecoded with **Hermes Agent** and **Gemini 3.8 Flash**.</sub>
