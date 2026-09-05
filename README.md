# Telegram Anti-NSFW & Heart Emoji Shield Bot (Serverless Edition) 🛡️

> 💡 **Looking for the traditional Python edition?**  
> Check out the original server-hosted repository: 👉 **[NotMmd/antinsfwbot](https://github.com/NotMmd/antinsfwbot)**

---

An advanced, automated Telegram moderation bot running **100% serverless** on **Telegram Serverless** (Telegram Cloud V8 sandbox with native SQLite). It detects single heart and suggestive emoji spam posted under newly published channel posts within a customizable time window (default: 30 minutes).

When detected, the bot instantly deletes the offending message, mutes the spammer, purges their original join message, and sends an alert with an interactive control panel (**Ban Group**, **Ban Channel**, **Ban Both**, **Unmute**, **Keep Muted**) to the admin's private chat.

---

## 🎯 Why This Bot Exists

Automated NSFW userbot accounts frequently target Telegram channel discussion groups by posting single heart/mouth emojis (`❤️`, `💗`, `❤️‍🔥`, `🫦`, `👄`) under newly published channel posts within minutes of release.

These spam bots aim to stay at the very top of the comment section so group members click their provocative profile pictures and bios, leading to NSFW promotional networks or phishing links.

This bot intercepts and eliminates this spam vector by:
1. **Timestamp Learning:** Records channel post timestamps and links them to group discussion thread roots automatically.
2. **Join Message Tracking:** Stores new member join service message IDs so they can be completely wiped if the user is banned.
3. **Automated Muting & Deletion:** Immediately removes the comment and restricts the spammer if sent within the target post window.
4. **Interactive Moderation:** Notifies the administrator with evidence, message details, profile links, and one-tap moderation buttons with safety confirmation prompts.

---

## ⚡ Why Serverless?

Traditionally, running a Telegram bot requires provisioning a VPS, setting up Docker or Python virtual environments, configuring `systemd` services, and keeping a process running 24/7.

**Telegram Serverless changes this completely:**
- **Zero Infrastructure:** No servers, no containers, no hosting costs.
- **Built-in Cloud SQLite:** The database is provisioned and managed directly by Telegram via `schema.js`.
- **Global Edge Execution:** Runs on Telegram's lightweight V8 isolates right next to Telegram's core Bot API data centers for minimum latency.
- **Atomic CLI Deploys:** Managed entirely with `@tgcloud/cli`.

---

## 📁 Project Structure

```
.
├── handlers/
│   ├── channel_post.js     # Records post publication timestamps
│   ├── message.js          # Detects spam, mutes offenders, sends admin alerts
│   └── callback_query.js   # Handles admin moderation actions & confirmations
├── lib/
│   └── config.js           # Target IDs, window & emoji normalizer
├── schema.js               # Database schema (posts, threads, join_messages)
├── package.json
└── README.md
```

---

## 🚀 Deployment Guide

### 1. Prerequisites
- [Node.js](https://nodejs.org) 18 or newer
- A Telegram bot created via [@BotFather](https://t.me/BotFather)

### 2. Enable Serverless on BotFather
1. Open [@BotFather](https://t.me/BotFather) and send `/mybots`.
2. Select your bot → **Serverless** → **Turn On**.
3. Navigate to **CLI Access** → **Access Token** and copy your token (`app...:...`).

### 3. Clone and Configure
```bash
git clone https://github.com/NotMmd/antinsfwbot-serverless.git
cd antinsfwbot-serverless
```

Open `lib/config.js` and set your IDs:
```javascript
export const CONFIG = {
  TARGET_GROUP_ID: -1001234567890,   // Your group chat ID
  TARGET_CHANNEL_ID: -1009876543210, // Your channel ID
  ADMIN_USER_ID: 123456789,          // Your Telegram User ID
  WINDOW_MINUTES: 30,                // Detection window (minutes)
};
```

### 4. Deploy to Telegram Cloud
Login with your Serverless CLI token:
```bash
npx @tgcloud/cli login
```

Push the project code:
```bash
npx @tgcloud/cli push
```

Apply database migrations:
```bash
npx @tgcloud/cli migrate --yes
```

Verify your webhook status:
```bash
npx @tgcloud/cli webhook
```

---

## 🔒 Permissions Required
Ensure the bot is added as an **Administrator** in:
- **Discussion Group:** `Delete Messages` and `Restrict Members` permissions.
- **Broadcast Channel:** `Restrict Members` / `Ban Users` permissions.

---

## 📄 License
[MIT](LICENSE)

---
<sub>⚡ Vibecoded with **Hermes Agent** and **Gemini 3.8 Flash**.</sub>
