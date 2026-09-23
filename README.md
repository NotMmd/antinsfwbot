# Telegram Anti-NSFW & Heart Emoji Shield Bot (Serverless Edition) 🛡️

> 💡 **Looking for the traditional Python edition?**  
> Check out the original server-hosted repository: 👉 **[NotMmd/antinsfwbot](https://github.com/NotMmd/antinsfwbot)**

---

An advanced, automated Telegram moderation bot running **100% serverless** on **Telegram Serverless** (Telegram Cloud V8 sandbox with native SQLite). It detects single heart and suggestive emoji spam posted under newly published channel posts within a customizable time window (default: 30 minutes).

When detected, the bot applies the configured auto-delete and auto-ban actions, purges the offender's original join message after a group ban, and can send an alert with an interactive moderation panel (**Ban Group**, **Ban Channel**, **Ban Both**, **Unmute**, **Keep Muted**) to the admin's private chat.

---

## 🎯 Why This Bot Exists

Automated NSFW userbot accounts frequently target Telegram channel discussion groups by posting single heart/mouth emojis (`❤️`, `💗`, `❤️‍🔥`, `🫦`, `👄`) under newly published channel posts within minutes of release.

These spam bots aim to stay at the very top of the comment section so group members click their provocative profile pictures and bios, leading to NSFW promotional networks or phishing links.

This bot intercepts and eliminates this spam vector by:
1. **Timestamp Learning:** Records channel post timestamps and links them to group discussion thread roots automatically.
2. **Join Message Tracking:** Stores new member join service message IDs so they can be completely wiped if the user is banned.
3. **Automated Moderation:** Deletes the comment and bans the sender according to the live auto-delete, auto-ban, and target-scope settings.
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
│   ├── message.js          # Detects spam, applies settings, and sends alerts
│   └── callback_query.js   # Handles settings and moderation actions
├── lib/
│   └── config.js           # Target IDs, window & emoji normalizer
├── schema.js               # Database schema (posts, threads, join_messages, settings)
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
  AUTO_BAN_ENABLED: true,            // Automatically ban detected spammers
  AUTO_DELETE_ENABLED: true,         // Delete detected spam comments
  BAN_SCOPE: 'group',                // 'group', 'channel', or 'both'
  ADMIN_NOTIFICATIONS_ENABLED: true, // Send detection alerts to the admin
};
```

### Admin Settings Panel

After deploying, the configured admin (`ADMIN_USER_ID`) can open a private chat with the bot and send `/settings` or `/panel`. The inline keyboard displays live values and saves changes to the Telegram Serverless SQLite `settings` table. Values not yet overridden in the panel use the defaults in `lib/config.js`.

- **Auto-Ban:** Ban the detected account in the selected target scope.
- **Delete Msg:** Delete the detected comment from the discussion group.
- **Target:** Cycle between Group only, Channel only, and Both.
- **Admin Alerts:** Forward the detected comment and send its moderation alert to the admin.

Detection continues to use the existing single-heart comment rule and `WINDOW_MINUTES` interval. Each setting can be changed at runtime without redeploying. The bot needs delete-message rights in the discussion group and ban-user rights in the configured group and/or channel for the selected actions to succeed.

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
- **Discussion Group:** `Delete Messages`, `Restrict Members` (for manual unmute controls), and `Ban Users` permissions when the selected scope includes the group.
- **Broadcast Channel:** `Ban Users` permission when the selected scope includes the channel.

---

## 📄 License
[MIT](LICENSE)

---
<sub>⚡ Vibecoded with **Hermes Agent** and **Gemini 3.8 Flash**.</sub>
