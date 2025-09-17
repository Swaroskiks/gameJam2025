"""
Module de gestion du temps diégétique pour A Day at the Office.
Horloge qui avance de 08:30 à 08:48 selon GAME_SECONDS_PER_REAL_SECOND.
"""

from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GameClock:
    """
    Horloge diégétique du jeu.
    
    Le temps avance de START_TIME à END_TIME selon le facteur de vitesse.
    Quand END_TIME est atteint, is_deadline() retourne True.
    """
    
    def __init__(self, start_time: str, end_time: str, speed: float = 5.0):
        """
        Initialise l'horloge de jeu.
        
        Args:
            start_time: Heure de début au format "HH:MM" (ex: "08:30")
            end_time: Heure de fin au format "HH:MM" (ex: "08:48")  
            speed: Facteur de vitesse (secondes de jeu par seconde réelle)
        """
        self.speed = speed
        self.start_time = self._parse_time(start_time)
        self.end_time = self._parse_time(end_time)
        self.current_time = self.start_time
        self.is_running = False
        self.total_real_seconds = 0.0
        # Dernière minute émise (HH:MM) pour TIME_TICK / TIME_REACHED
        self._last_minute_emitted: Optional[str] = None
        
        logger.info(f"GameClock initialized: {start_time} -> {end_time} (speed: {speed}x)")
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse une chaîne "HH:MM" en datetime."""
        try:
            hour, minute = map(int, time_str.split(':'))
            # Utilise une date fixe (11 septembre 2001)
            return datetime(2001, 9, 11, hour, minute, 0)
        except ValueError as e:
            logger.error(f"Invalid time format '{time_str}': {e}")
            raise
    
    def start(self) -> None:
        """Démarre l'horloge."""
        self.is_running = True
        logger.info("GameClock started")
    
    def stop(self) -> None:
        """Arrête l'horloge."""
        self.is_running = False
        logger.info("GameClock stopped")
    
    def reset(self) -> None:
        """Remet l'horloge à l'heure de début."""
        self.current_time = self.start_time
        self.total_real_seconds = 0.0
        logger.info("GameClock reset")
    
    def tick(self, dt: float) -> None:
        """
        Met à jour l'horloge avec le delta time.
        
        Args:
            dt: Temps écoulé en secondes réelles depuis le dernier tick
        """
        if not self.is_running or self.is_deadline():
            return
        
        self.total_real_seconds += dt
        game_seconds = dt * self.speed
        self.current_time += timedelta(seconds=game_seconds)
        
        # S'assurer qu'on ne dépasse pas l'heure de fin
        if self.current_time > self.end_time:
            self.current_time = self.end_time
            self.stop()
            logger.warning("Deadline reached - GameClock stopped")

        # Émettre un événement à chaque changement de minute in-game
        try:
            from src.core.event_bus import event_bus  # import local pour éviter import cycles
            minute_str = self.current_time.strftime("%H:%M")
            if minute_str != self._last_minute_emitted:
                self._last_minute_emitted = minute_str
                # TIME_TICK toutes les minutes
                event_bus.emit("TIME_TICK", {"time": minute_str})
                # TIME_REACHED générique et spécifique
                event_bus.emit("TIME_REACHED", {"time": minute_str})
                event_bus.emit(f"TIME_REACHED:{minute_str}", {"time": minute_str})
        except Exception:
            # L'EventBus est optionnel; ignorer silencieusement si indisponible
            pass
    
    def get_time(self) -> datetime:
        """Retourne l'heure actuelle du jeu."""
        return self.current_time
    
    def get_time_str(self) -> str:
        """Retourne l'heure actuelle au format "HH:MM"."""
        return self.current_time.strftime("%H:%M")
    
    def get_detailed_time_str(self) -> str:
        """Retourne l'heure actuelle au format "HH:MM:SS"."""
        return self.current_time.strftime("%H:%M:%S")
    
    def is_deadline(self) -> bool:
        """Retourne True si l'heure de fin est atteinte."""
        return self.current_time >= self.end_time
    
    def get_progress(self) -> float:
        """
        Retourne le pourcentage de progression (0.0 à 1.0).
        
        Returns:
            Float entre 0.0 (début) et 1.0 (fin)
        """
        total_duration = (self.end_time - self.start_time).total_seconds()
        elapsed = (self.current_time - self.start_time).total_seconds()
        return min(1.0, elapsed / total_duration) if total_duration > 0 else 1.0
    
    def get_remaining_time(self) -> timedelta:
        """Retourne le temps restant avant la deadline."""
        if self.is_deadline():
            return timedelta(0)
        return self.end_time - self.current_time
    
    def get_remaining_minutes(self) -> int:
        """Retourne le nombre de minutes restantes."""
        remaining = self.get_remaining_time()
        return int(remaining.total_seconds() / 60)
    
    def format_time(self, time_obj: Optional[datetime] = None) -> str:
        """
        Formate un temps pour l'affichage.
        
        Args:
            time_obj: Objet datetime à formater, ou None pour l'heure actuelle
            
        Returns:
            Chaîne formatée "HH:MM"
        """
        if time_obj is None:
            time_obj = self.current_time
        return time_obj.strftime("%H:%M")
    
    def is_time_before(self, target_time: str) -> bool:
        """
        Vérifie si l'heure actuelle est avant l'heure cible.
        
        Args:
            target_time: Heure cible au format "HH:MM"
            
        Returns:
            True si l'heure actuelle est avant l'heure cible
        """
        target = self._parse_time(target_time)
        return self.current_time < target
    
    def is_time_after(self, target_time: str) -> bool:
        """
        Vérifie si l'heure actuelle est après l'heure cible.
        
        Args:
            target_time: Heure cible au format "HH:MM"
            
        Returns:
            True si l'heure actuelle est après l'heure cible
        """
        target = self._parse_time(target_time)
        return self.current_time > target
    
    def get_elapsed_real_time(self) -> float:
        """Retourne le temps réel écoulé en secondes."""
        return self.total_real_seconds
    
    def __str__(self) -> str:
        """Représentation string de l'horloge."""
        status = "RUNNING" if self.is_running else "STOPPED"
        return f"GameClock({self.get_time_str()} - {status})"
