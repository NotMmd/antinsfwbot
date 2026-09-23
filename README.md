# Telegram Anti-NSFW Shield Bot 🛡️

An advanced, multi-branch Telegram moderation bot engineered to permanently solve the automated NSFW comment and funnel spam epidemic across discussion groups and community channels.

---

## 💡 The Core Limitation & The System One Solution

### Why Text & Emoji Matching Falls Short
Other editions of this bot (like `classic` or the serverless variants) rely on matching specific emojis (like single hearts) sent right after a channel post. While simple and zero-cost, text-based matching has inherent limitations:
1. **Bots Don't Only Send Emojis:** Some spam bots post regular text instead of emojis, slipping right past emoji filters.
2. **Humans Send Emojis Too:** Real community members often react with a heart or expressive emoji under a new channel post. Blindly muting based on message content catches genuine users.

### The Real Vulnerability: Profile & Personal Channel Funnels
Modern Telegram NSFW bots don't need explicit words in the comments. The comment itself is just bait to get a high spot under the post. The real payload lives on their account:
- Their Telegram profile has an attached **Personal Channel (`personal_chat`)**.
- That personal channel hosts explicit previews, teaser media, and phishing/funnel links.

### The System One Architecture (`mtproto` branch)
Instead of guessing from the comment text, the **`mtproto`** branch uses **MTProto** alongside **System One decision models** (such as TypeSafe Jev, Convai Laya, or any compatible System One engine):
- 🔍 **Deep Profile Inspection:** Fetches the sender's bio, personal channel title, and channel username.
- 📩 **Channel Post Verification:** Reads the pinned/preview message directly from their attached channel.
- 🧠 **Instant Probabilistic Judgment (`noul`):** Passes structured profile and channel metadata to a System One decision engine. System One models make calibrated binary/probabilistic decisions in single-digit milliseconds without generative text overhead, costing fractions of a cent (or completely free when running an open-weights model locally).
- 🔌 **Pluggable Engine Interface:** Built around a modular router. You aren't locked into one provider — easily configure models like **Jev**, **Laya**, or plug in custom System One decision endpoints via `.env` or the live in-bot panel.
- 🚫 **Text-Agnostic Moderation:** Whether the bot leaves an emoji, a greeting, or regular text, the underlying adult funnel is identified and moderated. Real members can freely react with emojis without getting muted.

---

## 🌿 Available Editions & Branches

This repository is maintained across dedicated branches tailored for different architectures and operational scales:

| Branch | Architecture & Runtime | Detection Engine | Cost & Speed | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **`mtproto`** ⭐ | Python (`pyrotgfork` MTProto) | **Pluggable System One AI** (Jev, Laya, etc.) + Deep Profile & Personal Channel Inspection | Millisecond latency, ultra-cheap (or free locally) | **Recommended:** Accurate, text-agnostic detection with zero false positives |
| **`classic`** | Python (`python-telegram-bot` v22+) | Window & Emoji Heuristics | Free (Heuristic-based) | Simple VPS setups without AI API keys |
| **`telegram-serverless`** | Node.js (V8 Isolation via `@tgcloud/cli`) | Window & Emoji Heuristics | Zero server cost (Telegram Cloud) | Running 100% on Telegram's official infrastructure |
| **`cloudflare-worker`** | JavaScript (Cloudflare Workers) | Window & Emoji Heuristics | Free tier Cloudflare edge | Edge-hosted webhook setups using Cloudflare D1 |

---

## ✨ Core Features

- 🧠 **Pluggable System One AI (`mtproto` branch):** Flexible router supporting System One models like **TypeSafe Jev**, **Convai Laya**, and custom decision engines.
- 🗄️ **Intelligent Verdict Cache:** Evaluated user IDs and verdicts are cached in SQLite to prevent duplicate API requests and ensure instantaneous repeat checks.
- 🧹 **Auto-Clean Join Messages:** Automatically identifies and purges `"User joined the group"` service messages when an offender is banned.
- ⚙️ **Interactive In-Bot Admin Panel:** Send `/settings` or `/panel` in private chat to dynamically toggle:
  - `[✅ Auto-Ban: ON / OFF]`
  - `[✅ Delete Msg: ON / OFF]`
  - `[🎯 Target Scope: Group / Channel / Both]`
  - `[🤖 AI Engine]` *(on `mtproto` branch: switch active System One engine)*
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
# Set API_ID, API_HASH, BOT_TOKEN, and your SYSTEM_ONE_ENGINE
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
