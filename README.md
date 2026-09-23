# AntiNSFWBot on Cloudflare Workers

Telegram moderation bot built as a standard ES module Worker. It receives webhook updates, tracks channel posts and discussion threads in D1, detects heart emoji messages in a configurable time window, optionally restricts users and deletes messages, and sends an admin alert with moderation actions.

## Requirements

- Node.js 20 or later and npm
- A Cloudflare account with Workers and D1 enabled
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- The numeric Telegram user ID for the bot administrator

## 1. Install and create the D1 database

```sh
npm install
npm run db:create
```

Copy the `database_id` printed by Wrangler into `wrangler.toml`, replacing `REPLACE_WITH_D1_DATABASE_ID`. Set `ADMIN_USER_ID` there too, replacing its placeholder. Keep `database_name` as `antinsfwbot-db`, or update it consistently in `wrangler.toml` and the package scripts.

Apply the initial schema locally and remotely:

```sh
npm run db:migrate:local
npm run db:migrate:remote
```

The migration is `migrations/0001_initial.sql`. To inspect databases or migration state:

```sh
npx wrangler d1 list
npx wrangler d1 migrations list antinsfwbot-db --local
npx wrangler d1 migrations list antinsfwbot-db --remote
```

## 2. Configure secrets and settings

For local development, copy `.dev.vars.example` to `.dev.vars` and set `BOT_TOKEN`, `WEBHOOK_SECRET`, and `ADMIN_USER_ID`:

```sh
cp .dev.vars.example .dev.vars
```

For production, add secrets through Wrangler. Do not put bot tokens in `wrangler.toml` or commit them:

```sh
npx wrangler secret put BOT_TOKEN
npx wrangler secret put WEBHOOK_SECRET
```

`ADMIN_USER_ID`, `WINDOW_MINUTES`, `AUTO_BAN`, `DELETE_MESSAGE`, `TARGET_SCOPE`, and `ADMIN_ALERTS` can be configured as Wrangler vars in `wrangler.toml`. D1 settings saved from the bot panel override these fallback values. A D1 setting stays authoritative until changed from the panel; changing a Wrangler fallback does not overwrite a saved setting.

## 3. Run locally

```sh
npm run dev
```

Wrangler prints a local URL. Point a Telegram webhook at a publicly reachable HTTPS tunnel to that URL plus `/webhook`, and set the same webhook secret as `WEBHOOK_SECRET`. The Worker also accepts updates at `/`.

## 4. Deploy and register the Telegram webhook

```sh
npm run deploy
```

Use the deployed `workers.dev` URL or a custom domain as the webhook endpoint. Register the webhook and secret token with Telegram (replace the values):

```sh
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -H 'content-type: application/json' \
  -d '{"url":"https://<YOUR_WORKER_HOST>/webhook","secret_token":"<WEBHOOK_SECRET>"}'
```

Telegram sends `X-Telegram-Bot-Api-Secret-Token`; the Worker checks it when `WEBHOOK_SECRET` is set. The secret token must use Telegram's accepted characters and length. Check registration with:

```sh
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
```

The bot needs permission to read messages and delete messages in the discussion group. To apply restrictions, promote it to an administrator with permission to restrict members. Channel posts must reach the bot as updates; add the bot to the channel as an administrator. Add it to the linked discussion group as well.

## Moderation behavior

- The Worker stores channel post IDs and timestamps, and associates group forum threads with a channel post when a forwarded channel message is replied to.
- For a group message it looks for a forwarded channel origin, then a stored discussion-thread association, then the latest stored channel post.
- A message or caption containing a recognized heart glyph qualifies when its timestamp is no more than `WINDOW_MINUTES` after that post.
- `AUTO_BAN=true` applies a one-hour restriction (mute) in the group. `DELETE_MESSAGE=true` deletes the message after attempting to forward it to the administrator. Both settings default to enabled.
- Admin alerts include buttons for a permanent ban, unmute, delete, or dismissal. The buttons are restricted to `ADMIN_USER_ID`.
- `TARGET_SCOPE` accepts `group`, `channel`, or `both`. Channel posts are saved for origin resolution; selecting `channel` also checks heart-bearing channel posts themselves. Telegram channel posts generally have no individual member to restrict.
- Admin moderation calls can fail if the bot lacks Telegram permissions. Failures are logged in Worker logs; they do not stop other actions.

## Admin settings panel

Open a private chat with the bot as the configured administrator and send `/settings` or `/panel`. Tap each inline button to cycle or toggle the setting. Changes are stored in D1 and the keyboard refreshes in place.

- **Auto-Ban**: apply or stop the automatic one-hour restriction in groups.
- **Delete Msg**: delete or retain qualifying group messages after the admin-forward attempt.
- **Target Scope**: cycle through group, channel, and both.
- **Admin Alerts**: send or stop forwarding and alerts to the admin.

The panel commands and callbacks are ignored or rejected for other Telegram accounts. To clear a saved setting and return to its environment fallback, remove it from D1:

```sh
npx wrangler d1 execute antinsfwbot-db --remote \
  --command="DELETE FROM settings WHERE key='auto_ban';"
```

Use one of `auto_ban`, `delete_message`, `admin_alerts`, or `target_scope` as the key.

## Wrangler scripts

- `npm run dev` — run the Worker locally
- `npm run deploy` — deploy the Worker
- `npm run db:create` — create the D1 database
- `npm run db:migrate:local` — apply migrations to local D1
- `npm run db:migrate:remote` — apply migrations to production D1
