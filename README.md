# Telegram Anti-NSFW Shield Bot 🛡️

An advanced, multi-branch Telegram moderation bot engineered to permanently solve the automated NSFW comment and funnel spam epidemic across discussion groups and community channels.

---

## 💡 The Problem & The Modern Solution

### Why Traditional Bots Fail
Traditional anti-spam solutions rely on naive regex, keyword filters, or static emoji triggers (such as muting anyone who posts a single heart under a channel post). This causes two fatal problems:
1. **High False Positives:** Legitimate community members cheering or reacting with emojis get unfairly muted.
2. **Easy Bypasses:** Spam bots constantly change tactics — switching emojis, posting short greetings, or using zero-width characters.

### The Real Vulnerability: Profile & Personal Channel Funnels
Modern Telegram NSFW bots do not post explicit text directly in comments. Instead, they act as funnels:
- They leave casual or innocent comments to secure the top spot.
- Their Telegram profile features an attached **Personal Channel (`personal_chat`)**.
- That personal channel hosts explicit previews, teaser media, and phishing/funnel links.

### The System One Breakthrough (`mtproto` branch)
By leveraging **MTProto** alongside specialized **System One decision models (TypeSafe Jev & Convai Laya)**, this bot inspects what standard Bot API bots cannot see:
- 🔍 **Deep Profile Inspection:** Fetches the sender's bio, personal channel title, and channel username.
- 📩 **Channel Post Verification:** Reads the pinned/preview message directly from their attached channel.
- 🧠 **Instant Probabilistic Judgment (`noul`):** Passes the structured context to a lightweight System One model. Instead of paying for costly generative LLMs, System One decision engines evaluate the funnel in single-digit milliseconds at negligible cost (or 100% free locally with Laya).
- 🚫 **Content-Agnostic Moderation:** Whether the bot posts a heart, a greeting, or random text, the underlying adult funnel is definitively identified and purged. Real users remain completely unaffected.

---

## 🌿 Available Editions & Branches

This repository is maintained across dedicated branches tailored for different architectures and operational scales:

| Branch | Architecture & Runtime | Detection Engine | Cost & Speed | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **`mtproto`** ⭐ | Python (`pyrotgfork` MTProto) | **System One AI (Jev / Laya)** + Deep Profile & Personal Channel Inspection | Ultra-low latency, penny-fractions (or free via local Laya) | **Recommended:** Accurate, content-agnostic detection with zero false positives |
| **`classic`** | Python (`python-telegram-bot` v22+) | Window & Emoji Heuristics | Free (Heuristic-based) | Simple VPS setups without AI API keys |
| **`telegram-serverless`** | Node.js (V8 Isolation via `@tgcloud/cli`) | Window & Emoji Heuristics | Zero server cost (Telegram Cloud) | Running 100% on Telegram's official infrastructure |
| **`cloudflare-worker`** | JavaScript (Cloudflare Workers) | Window & Emoji Heuristics | Free tier Cloudflare edge | Edge-hosted webhook setups using Cloudflare D1 |

---

## ✨ Core Features

- 🧠 **Multi-Engine System One AI (`mtproto` branch):** Interacts natively with **TypeSafe Jev** and **Convai Laya** engines to make calibrated spam judgments.
- 🗄️ **Intelligent Verdict Cache:** Evaluated user IDs and verdicts are cached in SQLite to prevent duplicate API requests and ensure instantaneous repeat checks.
- 🧹 **Auto-Clean Join Messages:** Automatically identifies and purges `"User joined the group"` service messages when an offender is banned.
- ⚙️ **Interactive In-Bot Admin Panel:** Send `/settings` or `/panel` in private chat to dynamically toggle:
  - `[✅ Auto-Ban: ON / OFF]`
  - `[✅ Delete Msg: ON / OFF]`
  - `[🎯 Target Scope: Group / Channel / Both]`
  - `[🤖 AI Engine: Jev / Laya]` *(on `mtproto` branch)*
  - `[🔔 Admin Alerts: ON / OFF]`
- 🚨 **Instant Admin Action Dashboard:** Detailed alerts sent to the admin's DM with direct buttons to Ban Group, Ban Channel, Ban Both, Unmute, or Dismiss.

---

## 🚀 Quickstart & Installation (by Branch)

### 🌟 Recommended: `mtproto` Branch (System One AI)
```bash
git clone -b mtproto https://github.com/NotMmd/antinsfwbot.git
cd antinsfwbot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set API_ID, API_HASH, BOT_TOKEN, and your SYSTEM_ONE_ENGINE (jev/laya)
python main.py
```

### Branch: `classic` (Python Telegram Bot)
```bash
git clone -b classic https://github.com/NotMmd/antinsfwbot.git
cd antinsfwbot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

### Branch: `telegram-serverless` (Telegram Official Cloud)
```bash
git clone -b telegram-serverless https://github.com/NotMmd/antinsfwbot.git
cd antinsfwbot
npm install
npx @tgcloud/cli push
npx @tgcloud/cli migrate --yes
```

### Branch: `cloudflare-worker` (Cloudflare Workers + D1)
```bash
git clone -b cloudflare-worker https://github.com/NotMmd/antinsfwbot.git
cd antinsfwbot
npm install
npx wrangler d1 create antinsfw-db
npx wrangler d1 migrations apply antinsfw-db --remote
npx wrangler secret put BOT_TOKEN
npm run deploy
```

---

## 📜 License

Distributed under the [MIT License](LICENSE).

---
<sub>⚡ Vibecoded with **Hermes Agent** and **Gemini 3.8 Flash**.</sub>
