# Telegram Anti-NSFW Shield Bot 🛡️ (`classic` edition)

An automated, robust Telegram moderation bot written in Python (`python-telegram-bot` v22+) engineered to eliminate automated NSFW comment and funnel spam under newly published channel posts.

---

## 🧭 Repository Branches & Editions

This repository provides multiple architectural editions tailored for different hosting environments:

| Branch | Architecture & Runtime | Detection Method | Storage | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **`classic`** (Current) | Python (`python-telegram-bot`) | Time Window + Emoji Heuristics | SQLite | Standard VPS / dedicated servers, standalone Python setups |
| **`mtproto`** ⭐ | Python (`pyrotgfork` MTProto) | **Pluggable System One AI** (Jev, Laya) + Profile & Channel Inspection | SQLite | **Most Accurate:** Text-agnostic funnel detection with zero false positives |
| **`telegram-serverless`** | Node.js (Telegram Cloud `@tgcloud/cli`) | Time Window + Emoji Heuristics | Native SQLite | 100% serverless, zero VPS cost, runs on Telegram infra |
| **`cloudflare-worker`** | JavaScript (Cloudflare Workers) | Time Window + Emoji Heuristics | Cloudflare D1 | Serverless edge deployment with webhook routing |

---

## 🎯 How the Classic Detection Works

### The Spam Pattern
Automated NSFW userbots monitor Telegram channels and immediately drop single heart or suggestive emojis (`❤️`, `🫦`, `👄`, etc.) in the discussion comments within seconds of a post going live. Their goal is to claim the topmost comment spot to attract clicks to their profiles.

### The Moderation Pipeline
1. **Root Timestamp Resolution:** Automatically resolves the original publication time of channel posts and discussion thread roots.
2. **Normalized Matching:** Strips Unicode variation selectors (VS15, VS16), zero-width characters, and joiners before comparing against a strict set of suggestive emojis.
3. **Time Window Gating:** Only flags messages sent within `WINDOW_MINUTES` of the post.
4. **Action & Alert:** Applies configured actions (mute or ban, message purge, join-message cleanup) and dispatches an interactive dashboard to admin DMs.

---

## ✨ Features

- 🎯 **Targeted Spam & Emoji Normalization:** Filters messages containing strictly single heart/suggestive emoji variants (`🩷❤️🧡💛💚🩵💙💜🖤🩶🤍🤎❤️‍🔥❤️‍🩹❣️💕💞💓💗💖💘💝🫦👄`).
- ⏱️ **Configurable Detection Window:** Fully customizable via `WINDOW_MINUTES` in `.env` (default: 30 minutes).
- 🧹 **Auto Clean Join Messages:** Automatically deletes the user's initial `"User joined the group"` service message upon ban.
- ⚙️ **Interactive In-Bot Settings Panel:** Send `/settings` or `/panel` in private chat with the bot to toggle settings live:
  - `[✅ Auto-Ban: ON / OFF]`
  - `[✅ Delete Msg: ON / OFF]`
  - `[🎯 Target Scope: Group / Channel / Both]`
  - `[🔔 Admin Alerts: ON / OFF]`
- 🚨 **Instant 1-Click Admin DM Dashboard:** Admin alerts include direct action buttons: **Ban Group**, **Ban Channel**, **Ban Both**, **Unmute**, **Keep Muted**.

---

## 🚀 Setup & Installation

### 1. Clone & Environment Setup
```bash
git clone -b classic https://github.com/NotMmd/antinsfwbot.git
cd antinsfwbot

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration (`.env`)
Copy the sample configuration:
```bash
cp .env.example .env
nano .env
```

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

- `BOT_TOKEN`: Telegram bot token from [@BotFather](https://t.me/BotFather).
- `TARGET_GROUP_ID`: Discussion group ID where comments are posted.
- `TARGET_CHANNEL_ID`: Linked channel ID whose posts trigger the window.
- `ADMIN_IDS`: Comma-separated list of admin user IDs allowed to access `/settings`.

### 3. Execution
```bash
python main.py
```

### 4. Running as a Systemd Service (Production)
Create `/etc/systemd/system/antinsfwbot.service`:
```ini
[Unit]
Description=Anti-NSFW Heart Emoji Telegram Bot (Classic)
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/antinsfwbot
ExecStart=/path/to/antinsfwbot/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now antinsfwbot
```

---

## 🔒 Required Bot Permissions

- **In Discussion Group:**
  - ✅ `Delete Messages`
  - ✅ `Restrict Members`
- **In Channel:**
  - ✅ `Administrator` (with user restrict rights if banning from channel)

---

## 📜 License

Distributed under the [MIT License](LICENSE).

---
<sub>⚡ Vibecoded with **Hermes Agent** and **Gemini 3.8 Flash**.</sub>
