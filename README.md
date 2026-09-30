# Telegram Anti-NSFW Shield Bot 🛡️ (`mtproto` edition)

An advanced Telegram moderation bot powered by **MTProto** (`pyrotgfork`) and **Pluggable System One AI decision engines** (such as TypeSafe Jev, Convai Laya, or custom endpoints).

---

## 💡 The Architectural Breakthrough: Why MTProto & System One?

### The Core Problem with Message-Based Moderation
Traditional moderation bots (including the `classic` edition of this bot) rely exclusively on scanning message text (e.g., detecting heart emojis). In practice, this causes two severe issues:
1. **Bots Don't Only Send Emojis:** Modern NSFW userbots frequently post regular greetings, casual remarks, or conversational bait to slip past emoji filters.
2. **Humans Send Emojis Too:** Genuine community members routinely post heart emojis to express support under new channel posts. Muting based on text alone causes annoying false positives.

### The Real Vector: Attached Personal Channels (`personal_chat`)
Modern adult bots don't post explicit text in comments. The comment is just bait to get a high spot under the post. The actual malicious payload lives on their account:
- Their Telegram profile has an attached **Personal Channel (`personal_chat`)**.
- That personal channel hosts explicit previews, teaser media, and phishing/funnel links.

Standard HTTP Bot API bots cannot inspect personal channels or deep profile metadata. **MTProto with a Bot Token unlocks this capability.**

### How the System One Engine Works
1. **Context Extraction:** When a comment is posted, the bot uses MTProto to fetch:
   - User profile details (`first_name`, `last_name`, `username`, `bio`)
   - Attached personal channel metadata (`title`, `username`)
   - Pinned/preview post text directly from that personal channel
2. **Pluggable Decision Routing (`classifier.py`):** Passes the structured JSON payload to a System One decision engine (**TypeSafe Jev** or **Convai Laya**).
3. **Instant Probabilistic Judgment (`noul`):** System One models return calibrated probabilities in single-digit milliseconds without generative text overhead, costing fractions of a cent (or completely free when running an open-weights model like Laya locally).
4. **Intelligent Verdict Cache:** Evaluated user IDs and verdicts are cached in SQLite so repeat checks require zero API overhead.

---

## 🧭 Repository Editions

| Branch | Architecture & Runtime | Detection Engine | Cost & Speed |
| :--- | :--- | :--- | :--- |
| **`mtproto`** (Current) ⭐ | Python (`pyrotgfork` MTProto) | **Pluggable System One AI** (Jev / Laya) + Deep Profile Inspection | Millisecond latency, ultra-cheap (or free locally) |
| **`classic`** | Python (`python-telegram-bot`) | Time Window + Emoji Heuristics | Free (Heuristic-based) |
| **`telegram-serverless`** | Node.js (Telegram Cloud `@tgcloud/cli`) | Time Window + Emoji Heuristics | Zero server cost (Telegram Cloud) |
| **`cloudflare-worker`** | JavaScript (Cloudflare Workers) | Time Window + Emoji Heuristics | Free tier Cloudflare edge + D1 |

---

## ⚙️ In-Bot Admin Settings Panel

In private chat with the bot, authorized admins can send `/settings` or `/panel` to dynamically toggle:
- `[✅ Auto-Ban: ON / OFF]` — Automatic ban upon positive detection
- `[✅ Delete Msg: ON / OFF]` — Delete offending comment
- `[🎯 Target Scope: Group / Channel / Both]` — Where bans are applied
- `[🤖 AI Engine: Jev / Laya]` — Toggle active System One decision engine on the fly
- `[🔔 Admin Alerts: ON / OFF]` — Detailed DM notifications with manual override buttons

---

## 🚀 Setup & Installation

### 1. Requirements & Virtual Environment
```bash
git clone -b mtproto https://github.com/NotMmd/antinsfwbot.git
cd antinsfwbot

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Configuration (`.env`)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
nano .env
```

```ini
API_ID=123456
API_HASH=your_telegram_api_hash
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ

# System One Engine Configuration
SYSTEM_ONE_ENGINE=jev
JEV_API_URL=https://api.typesafe.ai/v1/judge
JEV_API_KEY=your_typesafe_key

# Optional: Laya Engine (for local or self-hosted endpoint)
LAYA_API_URL=http://localhost:8000/classify
LAYA_API_KEY=

DATABASE_PATH=bot.sqlite3
ADMIN_IDS=123456789
```

- `API_ID` & `API_HASH`: Obtained from [my.telegram.org](https://my.telegram.org).
- `BOT_TOKEN`: From [@BotFather](https://t.me/BotFather).
- `SYSTEM_ONE_ENGINE`: `jev` or `laya` (can also be toggled live via `/settings`).

### 3. Execution
```bash
python main.py
```

### 4. Systemd Service (Production)
```ini
[Unit]
Description=Anti-NSFW Shield Bot (MTProto + System One)
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

## 📜 License

Distributed under the [MIT License](LICENSE).

---
<sub>⚡ Vibecoded with **Hermes Agent** and **Gemini 3.8 Flash**.</sub>
