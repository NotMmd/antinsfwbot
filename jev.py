"""Jev classifier integration and Telegram context normalization."""

import asyncio
import json
from typing import Any, Callable, Mapping
from urllib.request import Request, urlopen


def _value(source: Any, key: str, default: Any = "") -> Any:
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _profile(source: Any) -> dict[str, str]:
    return {
        key: str(_value(source, key, "") or "")
        for key in ("first_name", "last_name", "username", "bio")
    }


def _channel(source: Any) -> dict[str, str]:
    return {
        "title": str(_value(source, "title", "") or ""),
        "username": str(_value(source, "username", "") or ""),
    }


def build_payload(
    comment_text: str,
    user: Any,
    personal_channel: Any = None,
    preview_text: str = "",
) -> dict[str, Any]:
    """Create the stable JSON payload required by Jev."""
    return {
        "comment": comment_text or "",
        "user": _profile(user),
        "personal_channel": _channel(personal_channel),
        "preview_text": preview_text or "",
    }


def _post_json(url: str, payload: dict[str, Any], api_key: str = "") -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urlopen(request, timeout=20) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not isinstance(result, dict) or not isinstance(result.get("verdict"), str):
        raise ValueError("Classifier response must be a JSON object with a string 'verdict'")
    return result


class HttpJsonClassifier:
    def __init__(
        self,
        api_url: str,
        api_key: str = "",
        transport: Callable[[str, dict[str, Any], str], dict[str, Any]] | None = None,
    ):
        self.api_url = api_url
        self.api_key = api_key
        self.transport = transport or _post_json

    async def classify(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_url:
            raise RuntimeError("JEV_API_URL is required to classify comments")
        result = await asyncio.to_thread(self.transport, self.api_url, payload, self.api_key)
        if not isinstance(result, dict) or not isinstance(result.get("verdict"), str):
            raise ValueError("Classifier response must contain a string 'verdict'")
        return result


class JevClassifier(HttpJsonClassifier):
    """Jev endpoint adapter using the shared JSON HTTP contract."""


async def collect_payload(client: Any, message: Any, database: Any) -> dict[str, Any]:
    """Read available Telegram profile/channel/post context without requiring optional fields."""
    sender = getattr(message, "from_user", None)
    user = _profile(sender)
    personal_channel = getattr(sender, "personal_channel", None) if sender else None
    full_user = None
    if sender and getattr(sender, "id", None):
        try:
            full_user = await client.get_chat(sender.id)
            user["bio"] = str(getattr(full_user, "bio", "") or "")
            personal_channel = getattr(full_user, "personal_channel", None) or personal_channel
        except Exception:
            pass
    channel_id = (
        getattr(full_user, "personal_channel_id", None)
        or (getattr(sender, "personal_channel_id", None) if sender else None)
    )
    if personal_channel is None and channel_id:
        try:
            personal_channel = await client.get_chat(channel_id)
        except Exception:
            pass
    elif isinstance(personal_channel, (int, str)):
        try:
            personal_channel = await client.get_chat(personal_channel)
        except Exception:
            personal_channel = None
    reply = getattr(message, "reply_to_message", None)
    preview = ""
    if reply:
        preview = getattr(reply, "text", None) or getattr(reply, "caption", None) or ""
    if not preview and reply:
        source_chat = getattr(reply, "forward_from_chat", None)
        source_id = getattr(reply, "forward_from_message_id", None)
        if source_chat and source_id:
            preview = database.get_post(source_chat.id, source_id) or ""
        if not preview:
            preview = database.get_post(message.chat.id, reply.id) or ""
    if not preview:
        try:
            chat = await client.get_chat(message.chat.id)
            pinned = getattr(chat, "pinned_message", None)
            if pinned:
                preview = getattr(pinned, "text", None) or getattr(pinned, "caption", None) or ""
        except Exception:
            pass
    text = getattr(message, "text", None) or getattr(message, "caption", None) or ""
    return build_payload(text, user, personal_channel, preview)
