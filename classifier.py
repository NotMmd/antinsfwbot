"""Small router for interchangeable System One classification engines."""

from typing import Any


class ClassifierRouter:
    def __init__(self, engines: dict[str, Any]):
        self.engines = engines

    async def classify(self, payload: dict[str, Any], engine: str = "jev") -> dict[str, Any]:
        try:
            selected = self.engines[engine]
        except KeyError as exc:
            raise ValueError(f"Unsupported System One engine: {engine}") from exc
        return await selected.classify(payload)
