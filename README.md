# Telegram Anti-NSFW Shield Bot 🛡️ (`telegram-serverless` edition)

An automated Telegram moderation bot running **100% serverless directly on Telegram Cloud infrastructure** via [`@tgcloud/cli`](https://www.npmjs.com/package/@tgcloud/cli).

No VPS, no Docker containers, and no external webhook servers required. Telegram executes the bot logic in isolated V8 sandboxes with native SQLite persistence.

---

## 🧭 Repository Editions

| Branch | Architecture & Runtime | Detection Engine | Storage | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **`telegram-serverless`** (Current) | Node.js (Telegram Cloud `@tgcloud/cli`) | Time Window + Emoji Heuristics | Native Telegram SQLite | 100% serverless, zero server maintenance |
| **`mtproto`** ⭐ | Python (`pyrotgfork` MTProto) | **Pluggable System One AI** (Jev, Laya) + Profile Inspection | SQLite | Highly accurate, text-agnostic AI funnel detection |
| **`classic`** | Python (`python-telegram-bot`) | Time Window + Emoji Heuristics | SQLite | Standard VPS setups |
| **`cloudflare-worker`** | JavaScript (Cloudflare Workers) | Time Window + Emoji Heuristics | Cloudflare D1 | Serverless edge deployment with Cloudflare |

---

## 🎯 Architecture & Workflow

- **Runtime:** Native V8 JavaScript sandbox (pure ES Modules).
- **Update Routing:** Direct event-driven webhook delivery to handlers (`handlers/message.js`, `handlers/callback_query.js`).
- **Database:** Native SQLite instance per bot managed via `@tgcloud/cli` and `schema.js`.
- **Live Settings Panel:** Authorized admin can use `/settings` or `/panel` in private chat to dynamically toggle settings:
  - `[✅ Auto-Ban: ON / OFF]`
  - `[✅ Delete Msg: ON / OFF]`
  - `[🎯 Target Scope: Group / Channel / Both]`
  - `[🔔 Admin Alerts: ON / OFF]`

---

## 🚀 Deployment Guide

### 1. Enable Serverless in BotFather
1. Open [@BotFather](https://t.me/BotFather) on Telegram.
2. Send `/mybots` → Select your bot.
3. Select **Serverless** → **Turn On**.
4. Go to **CLI Access** → Generate your CLI token (format: `app<bot_id>:<token>`).

### 2. Clone & Configure
```bash
git clone -b telegram-serverless https://github.com/NotMmd/antinsfwbot.git
cd antinsfwbot

npm install
```

Set your channel, group, and admin IDs in `lib/config.js`:
```javascript
export const CONFIG = {
  TARGET_GROUP_ID: -1001234567890,
  TARGET_CHANNEL_ID: -1001234567891,
  ADMIN_USER_ID: 123456789,
  WINDOW_MINUTES: 30,
  AUTO_BAN_ENABLED: false,
  AUTO_DELETE_ENABLED: true,
  BAN_SCOPE: 'group',
  ADMIN_NOTIFICATIONS_ENABLED: true,
};
```

Authenticate with `@tgcloud/cli`:
```bash
mkdir -p .tgcloud
cat << 'CREDS' > .tgcloud/credentials
{
  "token": "app123456789:your_access_token"
}
CREDS
chmod 600 .tgcloud/credentials
```

### 3. Deploy to Telegram Cloud
```bash
# Push code
npx @tgcloud/cli push

# Apply schema migrations
npx @tgcloud/cli migrate --yes

# Verify webhook status
npx @tgcloud/cli webhook
```

---

## ⚠️ Important Configuration Notes

- **Group Privacy Mode:** In `@BotFather`, ensure Group Privacy is turned OFF (`/mybots` → Select Bot → **Bot Settings** → **Group Privacy** → **Turn off**) so the bot receives group messages.
- **Anonymous Admin:** Do not set the bot as an anonymous administrator (`is_anonymous: True`), as Telegram suppresses regular message updates to anonymous admin webhooks.

---

## 📜 License

Distributed under the [MIT License](LICENSE).

---
<sub>⚡ Vibecoded with **Hermes Agent** and **Gemini 3.8 Flash**.</sub>
