# Telegram Anti-NSFW Shield Bot 🛡️ (`cloudflare-worker` edition)

An automated, ultra-fast Telegram moderation bot deployed on **Cloudflare Workers** with persistent storage powered by **Cloudflare D1**.

Delivers global low-latency execution, zero server maintenance, and full free-tier compatibility on Cloudflare's edge network.

---

## 🧭 Repository Editions

| Branch | Architecture & Runtime | Detection Engine | Storage | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **`cloudflare-worker`** (Current) | JavaScript (Cloudflare Workers) | Time Window + Emoji Heuristics | Cloudflare D1 | Serverless edge deployment, generous free tier |
| **`mtproto`** ⭐ | Python (`pyrotgfork` MTProto) | **Pluggable System One AI** (Jev, Laya) + Profile Inspection | SQLite | Highly accurate, text-agnostic AI funnel detection |
| **`classic`** | Python (`python-telegram-bot`) | Time Window + Emoji Heuristics | SQLite | Standard VPS setups |
| **`telegram-serverless`** | Node.js (Telegram Cloud `@tgcloud/cli`) | Time Window + Emoji Heuristics | Native SQLite | 100% serverless directly inside Telegram infrastructure |

---

## 🎯 Architecture Highlights

- **Standard Fetch Handler:** Processes incoming Telegram updates via `POST /webhook` (or root `/`).
- **Webhook Security:** Verifies incoming requests against `X-Telegram-Bot-Api-Secret-Token`.
- **Edge Storage (D1):** Stores posts, thread mappings, join message records, and live admin panel settings.
- **In-Bot Live Panel:** Authorized admins can send `/settings` or `/panel` in private chat to toggle:
  - `[Auto-Ban: ON / OFF]`
  - `[Delete Msg: ON / OFF]`
  - `[Target Scope: Group / Channel / Both]`
  - `[Admin Alerts: ON / OFF]`

---

## 🚀 Setup & Deployment

### 1. Prerequisites
- [Node.js](https://nodejs.org) installed
- A Cloudflare account with the [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### 2. Installation
```bash
git clone -b cloudflare-worker https://github.com/NotMmd/antinsfwbot.git
cd antinsfwbot

npm install
```

### 3. Initialize Cloudflare D1 Database
Create the database:
```bash
npx wrangler d1 create antinsfw-db
```
Copy the returned `database_id` and update `wrangler.toml`:
```toml
[[d1_databases]]
binding = "DB"
database_name = "antinsfw-db"
database_id = "your-database-id-here"
```

Apply database migrations:
```bash
# Local testing
npx wrangler d1 migrations apply antinsfw-db --local

# Production
npx wrangler d1 migrations apply antinsfw-db --remote
```

### 4. Configure Secrets & Environment
Set your production bot token:
```bash
npx wrangler secret put BOT_TOKEN
```

Optionally set a secret token for webhook verification:
```bash
npx wrangler secret put WEBHOOK_SECRET
```

Configure your environment variables in `wrangler.toml`:
```toml
[vars]
TARGET_GROUP_ID = "-1001234567890"
TARGET_CHANNEL_ID = "-1001234567891"
ADMIN_USER_ID = "123456789"
WINDOW_MINUTES = "30"
AUTO_BAN = "false"
DELETE_MESSAGE = "true"
TARGET_SCOPE = "both"
ADMIN_ALERTS = "true"
```

### 5. Deploy & Set Webhook
Deploy to Cloudflare Workers:
```bash
npm run deploy
```

Register your worker URL with Telegram:
```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://<YOUR_WORKER_NAME>.<YOUR_SUBDOMAIN>.workers.dev/webhook",
    "secret_token": "<YOUR_WEBHOOK_SECRET>"
  }'
```

Verify webhook status:
```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
```

---

## 📜 License

Distributed under the [MIT License](LICENSE).

---
<sub>⚡ Vibecoded with **Hermes Agent** and **Gemini 3.8 Flash**.</sub>
