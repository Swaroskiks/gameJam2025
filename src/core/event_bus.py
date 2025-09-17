"""
Minimal EventBus to orchestrate gameplay events.
"""

from typing import Callable, Dict, List, Any


class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def emit(self, event_type: str, payload: Dict[str, Any] | None = None) -> None:
        for handler in self._subscribers.get(event_type, []):
            try:
                handler(payload or {})
            except Exception:
                pass


event_bus = EventBus()


