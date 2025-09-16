"""
Système d'ascenseur pour A Day at the Office.
Gère le mouvement, les portes, et les animations de l'ascenseur.
"""

import logging
from typing import Optional, List, Callable
from enum import Enum
import pygame
from src.settings import MIN_FLOOR, MAX_FLOOR
from src.core.utils import clamp, lerp

logger = logging.getLogger(__name__)


class ElevatorState(Enum):
    """États possibles de l'ascenseur."""
    IDLE = "idle"
    MOVING_UP = "moving_up"
    MOVING_DOWN = "moving_down"
    OPENING_DOORS = "opening_doors"
    CLOSING_DOORS = "closing_doors"
    DOORS_OPEN = "doors_open"


class Elevator:
    """
    Système d'ascenseur avec gestion des portes et du mouvement.
    """
    
    def __init__(self, x: int = 64):
        self.x = x  # Position X de l'ascenseur
        self.current_floor = MIN_FLOOR  # Étage actuel
        self.target_floor = MIN_FLOOR   # Étage de destination
        self.state = ElevatorState.IDLE
        
        # Animation et timing
        self.animation_time = 0.0
        self.door_animation_duration = 1.0  # Temps pour ouvrir/fermer les portes
        self.floor_travel_time = 2.0        # Temps pour monter/descendre d'un étage
        
        # Position interpolée pour l'animation
        self.display_floor = float(self.current_floor)
        
        # File d'attente des appels
        self.call_queue: List[int] = []
        
        # Callbacks pour les événements
        self.on_floor_reached: Optional[Callable[[int], None]] = None
        self.on_doors_opened: Optional[Callable[[], None]] = None
        self.on_doors_closed: Optional[Callable[[], None]] = None
        
        # Statistiques
        self.total_uses = 0
        self.floors_visited: set[int] = set()
        
        logger.info(f"Elevator initialized at floor {self.current_floor}")
    
    def call(self, floor: int) -> bool:
        """
        Appelle l'ascenseur à un étage.
        
        Args:
            floor: Numéro de l'étage
            
        Returns:
            True si l'appel a été enregistré
        """
        if not self._is_valid_floor(floor):
            logger.warning(f"Invalid floor number: {floor}")
            return False
        
        if floor == self.current_floor and self.state == ElevatorState.IDLE:
            # Déjà à l'étage, juste ouvrir les portes
            self._start_opening_doors()
            return True
        
        # Ajouter à la file d'attente si pas déjà présent
        if floor not in self.call_queue:
            self.call_queue.append(floor)
            logger.info(f"Elevator called to floor {floor}")
        
        # Démarrer le mouvement si l'ascenseur est libre
        if self.state == ElevatorState.IDLE:
            self._process_next_call()
        
        return True
    
    def go_to(self, floor: int) -> bool:
        """
        Va directement à un étage (sélection depuis l'intérieur).
        
        Args:
            floor: Étage de destination
            
        Returns:
            True si la destination a été définie
        """
        if not self._is_valid_floor(floor):
            return False
        
        # Priorité absolue - vider la queue et aller directement
        self.call_queue.clear()
        self.call_queue.append(floor)
        
        if self.state == ElevatorState.DOORS_OPEN:
            # Fermer les portes puis bouger
            self._start_closing_doors()
        elif self.state == ElevatorState.IDLE:
            self._process_next_call()
        
        self.total_uses += 1
        logger.info(f"Elevator going to floor {floor}")
        return True
    
    def update(self, dt: float) -> None:
        """
        Met à jour l'état de l'ascenseur.
        
        Args:
            dt: Temps écoulé depuis la dernière frame
        """
        self.animation_time += dt
        
        if self.state == ElevatorState.MOVING_UP:
            self._update_moving_up(dt)
        elif self.state == ElevatorState.MOVING_DOWN:
            self._update_moving_down(dt)
        elif self.state == ElevatorState.OPENING_DOORS:
            self._update_opening_doors()
        elif self.state == ElevatorState.CLOSING_DOORS:
            self._update_closing_doors()
        elif self.state == ElevatorState.DOORS_OPEN:
            # Les portes restent ouvertes, rien à faire
            pass
        elif self.state == ElevatorState.IDLE:
            # Traiter les appels en attente
            if self.call_queue:
                self._process_next_call()
    
    def _update_moving_up(self, dt: float) -> None:
        """Met à jour le mouvement vers le haut."""
        floors_to_travel = self.target_floor - self.current_floor
        total_time = abs(floors_to_travel) * self.floor_travel_time
        
        if self.animation_time >= total_time:
            # Arrivé à destination
            self.current_floor = self.target_floor
            self.display_floor = float(self.current_floor)
            self.floors_visited.add(self.current_floor)
            self._start_opening_doors()
            
            if self.on_floor_reached:
                self.on_floor_reached(self.current_floor)
        else:
            # Interpoler la position d'affichage
            progress = self.animation_time / total_time
            start_floor = self.target_floor - floors_to_travel
            self.display_floor = lerp(start_floor, self.target_floor, progress)
    
    def _update_moving_down(self, dt: float) -> None:
        """Met à jour le mouvement vers le bas."""
        floors_to_travel = self.current_floor - self.target_floor
        total_time = floors_to_travel * self.floor_travel_time
        
        if self.animation_time >= total_time:
            # Arrivé à destination
            self.current_floor = self.target_floor
            self.display_floor = float(self.current_floor)
            self.floors_visited.add(self.current_floor)
            self._start_opening_doors()
            
            if self.on_floor_reached:
                self.on_floor_reached(self.current_floor)
        else:
            # Interpoler la position d'affichage
            progress = self.animation_time / total_time
            start_floor = self.target_floor + floors_to_travel
            self.display_floor = lerp(start_floor, self.target_floor, progress)
    
    def _update_opening_doors(self) -> None:
        """Met à jour l'ouverture des portes."""
        if self.animation_time >= self.door_animation_duration:
            self.state = ElevatorState.DOORS_OPEN
            if self.on_doors_opened:
                self.on_doors_opened()
            logger.debug("Elevator doors opened")
    
    def _update_closing_doors(self) -> None:
        """Met à jour la fermeture des portes."""
        if self.animation_time >= self.door_animation_duration:
            self.state = ElevatorState.IDLE
            if self.on_doors_closed:
                self.on_doors_closed()
            
            # Traiter l'appel suivant
            if self.call_queue:
                self._process_next_call()
            
            logger.debug("Elevator doors closed")
    
    def _start_opening_doors(self) -> None:
        """Démarre l'animation d'ouverture des portes."""
        self.state = ElevatorState.OPENING_DOORS
        self.animation_time = 0.0
        logger.debug("Elevator doors opening")
    
    def _start_closing_doors(self) -> None:
        """Démarre l'animation de fermeture des portes."""
        self.state = ElevatorState.CLOSING_DOORS
        self.animation_time = 0.0
        logger.debug("Elevator doors closing")
    
    def _process_next_call(self) -> None:
        """Traite le prochain appel dans la file d'attente."""
        if not self.call_queue:
            return
        
        # Prendre le premier appel (FIFO pour simplicité)
        next_floor = self.call_queue.pop(0)
        
        if next_floor == self.current_floor:
            # Déjà au bon étage, juste ouvrir les portes
            self._start_opening_doors()
            return
        
        # Démarrer le mouvement
        self.target_floor = next_floor
        self.animation_time = 0.0
        
        if next_floor > self.current_floor:
            self.state = ElevatorState.MOVING_UP
            logger.info(f"Elevator moving up: {self.current_floor} -> {next_floor}")
        else:
            self.state = ElevatorState.MOVING_DOWN
            logger.info(f"Elevator moving down: {self.current_floor} -> {next_floor}")
    
    def _is_valid_floor(self, floor: int) -> bool:
        """
        Vérifie si un numéro d'étage est valide.
        
        Args:
            floor: Numéro d'étage à vérifier
            
        Returns:
            True si l'étage est valide
        """
        return MIN_FLOOR <= floor <= MAX_FLOOR
    
    def is_at_floor(self, floor: int) -> bool:
        """
        Vérifie si l'ascenseur est à un étage donné.
        
        Args:
            floor: Numéro d'étage
            
        Returns:
            True si l'ascenseur est à cet étage
        """
        return self.current_floor == floor and self.state in [
            ElevatorState.IDLE, 
            ElevatorState.DOORS_OPEN,
            ElevatorState.OPENING_DOORS,
            ElevatorState.CLOSING_DOORS
        ]
    
    def is_moving(self) -> bool:
        """
        Vérifie si l'ascenseur est en mouvement.
        
        Returns:
            True si l'ascenseur bouge
        """
        return self.state in [ElevatorState.MOVING_UP, ElevatorState.MOVING_DOWN]
    
    def are_doors_open(self) -> bool:
        """
        Vérifie si les portes sont ouvertes.
        
        Returns:
            True si les portes sont ouvertes
        """
        return self.state == ElevatorState.DOORS_OPEN
    
    def can_enter(self) -> bool:
        """
        Vérifie si on peut entrer dans l'ascenseur.
        
        Returns:
            True si on peut entrer
        """
        return self.state == ElevatorState.DOORS_OPEN
    
    def force_close_doors(self) -> bool:
        """
        Force la fermeture des portes si elles sont ouvertes.
        
        Returns:
            True si les portes ont commencé à se fermer
        """
        if self.state == ElevatorState.DOORS_OPEN:
            self._start_closing_doors()
            return True
        return False
    
    def get_display_position(self) -> float:
        """
        Retourne la position d'affichage interpolée de l'ascenseur.
        
        Returns:
            Position flottante pour l'animation fluide
        """
        return self.display_floor
    
    def get_door_animation_progress(self) -> float:
        """
        Retourne le progrès de l'animation des portes (0.0 à 1.0).
        
        Returns:
            Progrès de l'animation
        """
        if self.state in [ElevatorState.OPENING_DOORS, ElevatorState.CLOSING_DOORS]:
            return clamp(self.animation_time / self.door_animation_duration, 0.0, 1.0)
        elif self.state == ElevatorState.DOORS_OPEN:
            return 1.0
        else:
            return 0.0
    
    def get_current_floor(self) -> int:
        """Retourne l'étage actuel."""
        return self.current_floor
    
    def get_target_floor(self) -> Optional[int]:
        """Retourne l'étage de destination ou None si stationnaire."""
        if self.is_moving():
            return self.target_floor
        return None
    
    def get_state(self) -> ElevatorState:
        """Retourne l'état actuel de l'ascenseur."""
        return self.state
    
    def get_queue_length(self) -> int:
        """Retourne le nombre d'appels en attente."""
        return len(self.call_queue)
    
    def clear_queue(self) -> None:
        """Vide la file d'attente des appels."""
        self.call_queue.clear()
        logger.debug("Elevator queue cleared")
    
    def get_stats(self) -> dict:
        """
        Retourne les statistiques d'utilisation.
        
        Returns:
            Dictionnaire avec les stats
        """
        return {
            "total_uses": self.total_uses,
            "floors_visited": len(self.floors_visited),
            "current_floor": self.current_floor,
            "state": self.state.value,
            "queue_length": len(self.call_queue)
        }
