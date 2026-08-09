# Telegram Anti-NSFW Heart Emoji Bot

An automated Telegram moderation bot written in Python (`python-telegram-bot` v22+) that detects single heart emoji spam sent under newly published channel posts within a customizable time window (default 20 minutes). When detected, the bot automatically deletes the message, mutes the user, and sends an alert with interactive action buttons (**Ban**, **Unmute**, **Keep Muted**) to the admin's DM.

---

### Why This Bot Exists

Automated NSFW bot accounts frequently target Telegram channel discussion groups by posting single heart emojis (`❤️`, `💗`, `❤️‍🔥`, etc.) under newly published channel posts within minutes of release. These userbots aim to stay top-of-comment so group members click their profile links, leading to NSFW promotion channels or malware distribution.

This bot stops that automated spam pattern at the source by immediately deleting single heart emoji comments sent within the first 15–20 minutes of publication and muting the account for admin review.

---

### Features

- 🎯 **Targeted Spam Prevention:** Filters messages containing ONLY a single heart emoji (`🩷❤️🧡💛💚🩵💙💜🖤🩶🤍🤎❤️‍🔥❤️‍🩹❣💕💞💓💗💖💘💝`).
- ⏱️ **Customizable Time Window:** Configurable via `WINDOW_MINUTES` environment variable (defaults to 20 minutes).
- 🛠️ **Emoji Variation Normalization:** Handles Unicode variation selectors (VS16, ZWJ) cleanly.
- 🗄️ **Persistent Thread Mapping:** SQLite database tracks channel posts and auto-forwarded discussion thread IDs across bot restarts.
- 🚨 **Admin DM Control Panel:** Forwards the offending message to the admin's direct message along with interactive action buttons (**Ban User**, **Unmute User**, **Keep Muted**).

---

### Origin & Credits

This project was **vibecoded** using **Gemini 3.6 Flash** and **Claude Opus 5** via Hermes Agent.

---

### Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NotMmd/antinsfwbot.git
   cd antinsfwbot
   ```

2. **Create a Python Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Copy `.env.example` to `.env` and fill in your values:
   ```bash
   cp .env.example .env
   ```

   ```ini
   BOT_TOKEN=YOUR_BOT_TOKEN_HERE
   TARGET_GROUP_ID=-1001234567890
   TARGET_CHANNEL_ID=-1001234567891
   ADMIN_DM_ID=123456789
   WINDOW_MINUTES=20
   DB_PATH=~/antinsfwbot/posts.db
   ```

---

### Running the Bot

#### Option 1: Direct Run (Development)
```bash
python main.py
```

#### Option 2: Systemd Service (Linux)
Create `/etc/systemd/system/antinsfwbot.service`:
```ini
[Unit]
Description=Anti-NSFW Heart Emoji Bot
After=network.target

[Service]
Type=simple
User=youruser
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

#### Option 3: Running with PM2

If you use **PM2** to manage your processes:

1. **Install PM2** (if not already installed):
   ```bash
   npm install -g pm2
   ```

2. **Start the bot using Python from the virtual environment:**
   ```bash
   pm2 start main.py --name "antinsfwbot" --interpreter ./venv/bin/python
   ```

3. **Save PM2 process list and configure autostart:**
   ```bash
   pm2 save
   pm2 startup
   ```

4. **Useful PM2 Commands:**
   - View logs: `pm2 logs antinsfwbot`
   - Check status: `pm2 status`
   - Restart bot: `pm2 restart antinsfwbot`

---

### Admin Bot Permissions

Ensure the bot is added to:
1. **Target Discussion Group:** Added as an Admin with permissions:
   - ✅ `Delete Messages`
   - ✅ `Restrict Members`
2. **Target Channel:** Added as an Admin.

---

### License

This project is licensed under the [MIT License](LICENSE).
