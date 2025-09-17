"""
Contrôleur de timeline orchestré par les événements temporels.

Lit src/data/timeline.json et émet des événements (via EventBus) aux heures prévues.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.settings import DATA_PATH
from src.core.utils import load_json_safe, parse_hhmm
from src.core.event_bus import event_bus, TIME_REACHED

logger = logging.getLogger(__name__)


@dataclass
class TimelineEvent:
    at: str
    emit: str
    fired: bool = False


class TimelineController:
    """
    Charge une timeline et déclenche des événements lorsqu'une minute correspond.
    Deux déclenchements possibles:
    - Pull: appeler update(clock) chaque frame
    - Push: écoute des TIME_REACHED du EventBus
    """

    def __init__(self) -> None:
        self.events: List[TimelineEvent] = []
        self._subscribed = False

    def load(self, path: Optional[Path] = None) -> bool:
        try:
            path = path or (DATA_PATH / "timeline.json")
            data = load_json_safe(path)
            self.events.clear()
            if data and isinstance(data.get("events"), list):
                for e in data["events"]:
                    if not isinstance(e, dict):
                        continue
                    at = e.get("at")
                    emit = e.get("emit")
                    if parse_hhmm(at) and isinstance(emit, str) and emit:
                        self.events.append(TimelineEvent(at=at, emit=emit))
            # S'abonner aux événements de temps
            if not self._subscribed:
                event_bus.subscribe(TIME_REACHED, self._on_time_reached)
                self._subscribed = True
            logger.info(f"Timeline loaded: {len(self.events)} events")
            return True
        except Exception as e:
            logger.error(f"Failed to load timeline: {e}")
            return False

    def _on_time_reached(self, payload: Dict[str, Any]) -> None:
        """Handler pour TIME_REACHED: {"time": "HH:MM"}."""
        try:
            time_str = (payload or {}).get("time")
            if not time_str:
                return
            for ev in self.events:
                if not ev.fired and ev.at == time_str:
                    self._fire(ev)
        except Exception:
            pass

    def update(self, game_clock) -> None:
        """
        Mode pull: vérifie l'heure et déclenche les événements manquants.
        """
        try:
            time_str = game_clock.get_time_str()
            for ev in self.events:
                if not ev.fired and ev.at == time_str:
                    self._fire(ev)
        except Exception:
            pass

    def _fire(self, ev: TimelineEvent) -> None:
        ev.fired = True
        # Émettre un événement de domaine ainsi qu'un canal namespacé
        event_bus.emit(ev.emit, {"at": ev.at})
        event_bus.emit(f"TIMELINE:{ev.emit}", {"at": ev.at})
        logger.info(f"Timeline event fired at {ev.at}: {ev.emit}")


