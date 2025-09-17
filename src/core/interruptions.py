"""
Gestionnaire d'interruptions légères.

Génère de petites interruptions (appels, collègues) selon un taux horaire.
Hooké via TIME_TICK; émet des événements de domaine simples.
"""

import logging
import random
from typing import Optional

from src.settings import INTERRUPTION_RATE
from src.core.event_bus import event_bus, TIME_TICK

logger = logging.getLogger(__name__)


class InterruptionManager:
    def __init__(self) -> None:
        self.active: bool = True
        self.base_rate: float = float(INTERRUPTION_RATE or 0.0)
        event_bus.subscribe(TIME_TICK, self._on_time_tick)

    def _on_time_tick(self, payload):
        if not self.active:
            return
        time_str = (payload or {}).get("time", "")
        # Fenêtre plus chargée 08:33–08:40
        rate = self.base_rate
        if "08:33" <= time_str <= "08:40":
            rate *= 2.0
        # Tirage simple
        if random.random() < rate:
            self._emit_random_interruption(time_str)

    def _emit_random_interruption(self, at: str) -> None:
        kinds = [
            ("INT_CALL", 0.3),
            ("INT_COLLEAGUE_PEN", 0.3),
            ("INT_URGENT_MAIL", 0.4),
        ]
        r = random.random()
        acc = 0.0
        chosen = kinds[-1][0]
        for k, p in kinds:
            acc += p
            if r <= acc:
                chosen = k
                break
        event_bus.emit(chosen, {"at": at})
        logger.debug(f"Interruption emitted at {at}: {chosen}")


