# AntinsfwBot MTProto

A PyroTGFork Telegram bot that sends discussion comments and available profile/post context to a Jev classification service. SQLite stores runtime settings, observed post previews, and verdicts.

## Setup

Use Python 3.10 or newer, install dependencies, copy `.env.example` to `.env`, and fill in Telegram and Jev credentials:

```sh
python -m pip install -r requirements.txt
set -a && . ./.env && set +a
python main.py
```

The Telegram client is created with `API_ID`, `API_HASH`, and `BOT_TOKEN`. `JEV_API_URL` and `LAYA_API_URL` configure the two System One HTTP endpoints; the endpoint selected by `SYSTEM_ONE_ENGINE` is used (`jev` by default). Their API keys are sent as Bearer tokens when set. `DATABASE_PATH` defaults to `bot.sqlite3`. Set `ADMIN_IDS` to comma-separated Telegram user IDs allowed to use `/settings`. If no IDs are configured, settings access is denied.

## Jev HTTP contract

The bot sends a JSON `POST` request with this shape:

```json
{
  "comment": "comment text",
  "user": {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "username": "ada",
    "bio": "profile bio"
  },
  "personal_channel": {"title": "Ada's channel", "username": "ada_posts"},
  "preview_text": "pinned or replied-to post text"
}
```

The selected System One endpoint must return a JSON object with a string `verdict`, such as `safe` or `nsfw`. Optional fields such as `confidence` and `reason` are retained in the verdict cache. Both engine adapters use this shared HTTP contract, so a Laya deployment can expose it through its own endpoint or bridge. HTTP calls time out after 20 seconds. Profile fields unavailable from Telegram are sent as empty strings.

## Runtime settings

An authorized user can send `/settings` to show the inline keyboard. Classification starts enabled; deletion of NSFW comments starts disabled. The panel can toggle between Jev and Laya. Settings persist in SQLite, and cached verdicts are ignored while classification is disabled. Channel post text/captions and pinned text are used as preview context when available.

## Tests

Run the standard-library unit suite with:

```sh
python -m unittest discover -s tests -v
```
