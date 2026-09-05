# Telegram Anti-NSFW Bot (Serverless Edition)

A high-performance Telegram moderation bot running directly on **Telegram Serverless** (Telegram Cloud V8 sandbox with built-in SQLite database).

> 💡 **Looking for the traditional Python version?**  
> Check out the original server-hosted repository: [NotMmd/antinsfwbot](https://github.com/NotMmd/antinsfwbot).

---

## ✨ Features

- **100% Serverless:** Executes on Telegram's official infrastructure. No servers, VPS, or containers needed.
- **Native Cloud SQLite:** Tracks channel post publication dates and group discussion threads directly inside Telegram Cloud DB (`schema.js`).
- **Precision Detection:** Normalizes unicode characters (strips invisible selectors, BOM, zero-width chars) to reliably detect single heart emojis.
- **Admin Control Panel:** Delivers interactive alerts to admin DMs with confirmation dialogs:
  - 🚷 Ban from Group
  - 🚫 Ban from Channel
  - 🔨 Ban from Both
  - 🔊 Unmute User
  - ❌ Keep Muted

---

## 📁 Project Structure

```
.
├── handlers/
│   ├── channel_post.js     # Stores channel post timestamps
│   ├── message.js          # Spam detection, muting & admin alert dispatch
│   └── callback_query.js   # Moderation action buttons & confirmations
├── lib/
│   └── config.js           # Target IDs, window & emoji normalizer
├── schema.js               # Database schema (posts, threads, join_messages)
└── package.json
```

---

## 🚀 Deployment Guide

### 1. Prerequisites
- [Node.js](https://nodejs.org) 18 or newer
- A bot registered via [@BotFather](https://t.me/BotFather)

### 2. Enable Serverless on BotFather
1. Open [@BotFather](https://t.me/BotFather) and send `/mybots`.
2. Select your bot → **Serverless** → **Turn On**.
3. Navigate to **CLI Access** → **Access Token** and copy the token (`app...:...`).

### 3. Clone and Configure
```bash
git clone https://github.com/NotMmd/antinsfwbot-serverless.git
cd antinsfwbot-serverless
```

Edit `lib/config.js` with your chat IDs:
```javascript
export const CONFIG = {
  TARGET_GROUP_ID: -1001234567890,   // Your discussion group ID
  TARGET_CHANNEL_ID: -1009876543210, // Your channel ID
  ADMIN_USER_ID: 123456789,          // Your Telegram user ID
  WINDOW_MINUTES: 30,                // Detection window (minutes)
};
```

### 4. Deploy to Telegram Cloud
Authenticate CLI:
```bash
npx @tgcloud/cli login
```

Push project modules:
```bash
npx @tgcloud/cli push
```

Run database migrations:
```bash
npx @tgcloud/cli migrate --yes
```

Inspect webhook status:
```bash
npx @tgcloud/cli webhook
```

---

## 🔒 Permissions Required
Promote the bot to **Administrator** in:
- **Group:** Requires `Delete Messages` and `Restrict Members` permissions.
- **Channel:** Requires `Restrict Members` / `Ban Users` permissions.

---

## 📄 License
[MIT](LICENSE)
