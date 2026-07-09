"""In-process event bus. Modules communicate through events, never direct imports.

Subscribe with a dotted topic ("asset.created") or wildcard suffix ("asset.*", "*").
"""

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

Handler = Callable[[str, dict[str, Any]], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._handlers[topic].append(handler)

    def emit(self, topic: str, payload: dict[str, Any] | None = None) -> None:
        payload = payload or {}
        for pattern, handlers in self._handlers.items():
            if not _matches(pattern, topic):
                continue
            for handler in handlers:
                try:
                    handler(topic, payload)
                except Exception:  # one bad handler never breaks the emitter
                    logger.exception("event handler failed: topic=%s handler=%s", topic, handler)


def _matches(pattern: str, topic: str) -> bool:
    if pattern == "*" or pattern == topic:
        return True
    return pattern.endswith(".*") and topic.startswith(pattern[:-1])


bus = EventBus()
