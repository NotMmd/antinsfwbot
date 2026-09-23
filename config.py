"""Environment based configuration for the bot."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Config:
    api_id: int
    api_hash: str
    bot_token: str
    database_path: str = "bot.sqlite3"
    jev_api_url: str = ""
    jev_api_key: str = ""
    laya_api_url: str = ""
    laya_api_key: str = ""
    system_one_engine: str = "jev"
    admin_ids: tuple[int, ...] = ()

    @classmethod
    def from_env(cls) -> "Config":
        missing = [key for key in ("API_ID", "API_HASH", "BOT_TOKEN") if not os.getenv(key)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        try:
            api_id = int(os.environ["API_ID"])
        except ValueError as exc:
            raise ValueError("API_ID must be an integer") from exc
        engine = os.getenv("SYSTEM_ONE_ENGINE", "jev").strip().lower()
        if engine not in {"jev", "laya"}:
            raise ValueError("SYSTEM_ONE_ENGINE must be 'jev' or 'laya'")
        return cls(
            api_id=api_id,
            api_hash=os.environ["API_HASH"],
            bot_token=os.environ["BOT_TOKEN"],
            database_path=os.getenv("DATABASE_PATH", "bot.sqlite3"),
            jev_api_url=os.getenv("JEV_API_URL", ""),
            jev_api_key=os.getenv("JEV_API_KEY", ""),
            laya_api_url=os.getenv("LAYA_API_URL", ""),
            laya_api_key=os.getenv("LAYA_API_KEY", ""),
            system_one_engine=engine,
            admin_ids=tuple(
                int(value.strip()) for value in os.getenv("ADMIN_IDS", "").split(",") if value.strip()
            ),
        )
