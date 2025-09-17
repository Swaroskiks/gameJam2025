"""
Système de triggers et zones d'interaction pour A Day at the Office.
Gère les zones spéciales, événements automatiques, et interactions contextuelles.
"""

import logging
from typing import List, Dict, Any, Optional, Callable, Tuple
from enum import Enum
from dataclasses import dataclass
import pygame
from src.core.utils import point_in_rect, distance

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Types de triggers possibles."""
    ENTER_ZONE = "enter_zone"      # Déclenché en entrant dans une zone
    EXIT_ZONE = "exit_zone"        # Déclenché en sortant d'une zone
    STAY_IN_ZONE = "stay_in_zone"  # Déclenché en restant dans une zone
    INTERACT_NEAR = "interact_near" # Déclenché par interaction proche
    TIME_BASED = "time_based"      # Déclenché à un moment précis
    TASK_COMPLETION = "task_completion"  # Déclenché par completion de tâche


@dataclass
class TriggerCondition:
    """Condition pour déclencher un trigger."""
    trigger_type: TriggerType
    zone_rect: Optional[pygame.Rect] = None
    radius: Optional[float] = None
    center_pos: Optional[Tuple[float, float]] = None
    time_condition: Optional[str] = None  # Format "HH:MM"
    task_id: Optional[str] = None
    stay_duration: float = 0.0  # Durée minimum pour STAY_IN_ZONE


class Trigger:
    """
    Trigger générique qui peut déclencher des événements.
    """
    
    def __init__(self, trigger_id: str, condition: TriggerCondition, 
                 callback: Callable[['Trigger'], None], repeatable: bool = False):
        self.id = trigger_id
        self.condition = condition
        self.callback = callback
        self.repeatable = repeatable
        
        # État
        self.triggered = False
        self.active = True
        
        # Pour les triggers STAY_IN_ZONE
        self.time_in_zone = 0.0
        self.player_in_zone = False
        
        logger.debug(f"Trigger created: {trigger_id} ({condition.trigger_type.value})")
    
    def update(self, dt: float, player_pos: Tuple[float, float], 
               current_time: str, completed_tasks: set) -> bool:
        """
        Met à jour le trigger et vérifie s'il doit se déclencher.
        
        Args:
            dt: Temps écoulé
            player_pos: Position du joueur
            current_time: Heure actuelle "HH:MM"
            completed_tasks: Set des tâches terminées
            
        Returns:
            True si le trigger s'est déclenché
        """
        if not self.active or (self.triggered and not self.repeatable):
            return False
        
        should_trigger = False
        
        if self.condition.trigger_type == TriggerType.ENTER_ZONE:
            should_trigger = self._check_enter_zone(player_pos)
        elif self.condition.trigger_type == TriggerType.EXIT_ZONE:
            should_trigger = self._check_exit_zone(player_pos)
        elif self.condition.trigger_type == TriggerType.STAY_IN_ZONE:
            should_trigger = self._check_stay_in_zone(dt, player_pos)
        elif self.condition.trigger_type == TriggerType.INTERACT_NEAR:
            # Ce trigger doit être déclenché manuellement via trigger_interaction
            pass
        elif self.condition.trigger_type == TriggerType.TIME_BASED:
            should_trigger = self._check_time_condition(current_time)
        elif self.condition.trigger_type == TriggerType.TASK_COMPLETION:
            should_trigger = self._check_task_completion(completed_tasks)
        
        if should_trigger:
            self._execute()
            return True
        
        return False
    
    def _check_enter_zone(self, player_pos: Tuple[float, float]) -> bool:
        """Vérifie le trigger d'entrée de zone."""
        if self.condition.zone_rect:
            in_zone = point_in_rect(player_pos, self.condition.zone_rect)
            if in_zone and not self.player_in_zone:
                self.player_in_zone = True
                return True
        elif self.condition.center_pos and self.condition.radius:
            in_zone = distance(player_pos, self.condition.center_pos) <= self.condition.radius
            if in_zone and not self.player_in_zone:
                self.player_in_zone = True
                return True
        return False
    
    def _check_exit_zone(self, player_pos: Tuple[float, float]) -> bool:
        """Vérifie le trigger de sortie de zone."""
        if self.condition.zone_rect:
            in_zone = point_in_rect(player_pos, self.condition.zone_rect)
            if not in_zone and self.player_in_zone:
                self.player_in_zone = False
                return True
        elif self.condition.center_pos and self.condition.radius:
            in_zone = distance(player_pos, self.condition.center_pos) <= self.condition.radius
            if not in_zone and self.player_in_zone:
                self.player_in_zone = False
                return True
        return False
    
    def _check_stay_in_zone(self, dt: float, player_pos: Tuple[float, float]) -> bool:
        """Vérifie le trigger de séjour dans une zone."""
        in_zone = False
        
        if self.condition.zone_rect:
            in_zone = point_in_rect(player_pos, self.condition.zone_rect)
        elif self.condition.center_pos and self.condition.radius:
            in_zone = distance(player_pos, self.condition.center_pos) <= self.condition.radius
        
        if in_zone:
            self.time_in_zone += dt
            if self.time_in_zone >= self.condition.stay_duration:
                return True
        else:
            self.time_in_zone = 0.0
        
        return False
    
    def _check_time_condition(self, current_time: str) -> bool:
        """Vérifie le trigger temporel."""
        return (self.condition.time_condition and 
                current_time == self.condition.time_condition)
    
    def _check_task_completion(self, completed_tasks: set) -> bool:
        """Vérifie le trigger de completion de tâche."""
        return (self.condition.task_id and 
                self.condition.task_id in completed_tasks)
    
    def _execute(self) -> None:
        """Exécute le trigger."""
        try:
            self.callback(self)
            self.triggered = True
            logger.info(f"Trigger executed: {self.id}")
        except Exception as e:
            logger.error(f"Error executing trigger {self.id}: {e}")
    
    def trigger_interaction(self) -> bool:
        """
        Déclenche manuellement un trigger d'interaction.
        
        Returns:
            True si le trigger s'est exécuté
        """
        if (self.condition.trigger_type == TriggerType.INTERACT_NEAR and 
            self.active and (not self.triggered or self.repeatable)):
            self._execute()
            return True
        return False
    
    def reset(self) -> None:
        """Remet le trigger à zéro."""
        self.triggered = False
        self.time_in_zone = 0.0
        self.player_in_zone = False
    
    def activate(self) -> None:
        """Active le trigger."""
        self.active = True
    
    def deactivate(self) -> None:
        """Désactive le trigger."""
        self.active = False


class TriggerManager:
    """
    Gestionnaire des triggers du jeu.
    """
    
    def __init__(self):
        self.triggers: Dict[str, Trigger] = {}
        self.floor_triggers: Dict[int, List[str]] = {}  # Triggers par étage
        
        logger.info("TriggerManager initialized")
    
    def add_trigger(self, trigger: Trigger, floor: Optional[int] = None) -> None:
        """
        Ajoute un trigger.
        
        Args:
            trigger: Trigger à ajouter
            floor: Étage associé (None pour global)
        """
        self.triggers[trigger.id] = trigger
        
        if floor is not None:
            if floor not in self.floor_triggers:
                self.floor_triggers[floor] = []
            self.floor_triggers[floor].append(trigger.id)
        
        logger.debug(f"Trigger added: {trigger.id} (floor: {floor})")
    
    def remove_trigger(self, trigger_id: str) -> bool:
        """
        Supprime un trigger.
        
        Args:
            trigger_id: ID du trigger
            
        Returns:
            True si le trigger a été supprimé
        """
        if trigger_id in self.triggers:
            del self.triggers[trigger_id]
            
            # Supprimer des listes d'étages
            for floor_list in self.floor_triggers.values():
                if trigger_id in floor_list:
                    floor_list.remove(trigger_id)
            
            logger.debug(f"Trigger removed: {trigger_id}")
            return True
        
        return False
    
    def update(self, dt: float, player_pos: Tuple[float, float], 
               current_floor: int, current_time: str, completed_tasks: set) -> List[str]:
        """
        Met à jour tous les triggers actifs.
        
        Args:
            dt: Temps écoulé
            player_pos: Position du joueur
            current_floor: Étage actuel
            current_time: Heure actuelle
            completed_tasks: Tâches terminées
            
        Returns:
            Liste des IDs des triggers déclenchés
        """
        triggered_ids = []
        
        # Triggers globaux
        for trigger in self.triggers.values():
            if trigger.update(dt, player_pos, current_time, completed_tasks):
                triggered_ids.append(trigger.id)
        
        # Triggers spécifiques à l'étage
        floor_trigger_ids = self.floor_triggers.get(current_floor, [])
        for trigger_id in floor_trigger_ids:
            if trigger_id in self.triggers:
                trigger = self.triggers[trigger_id]
                if trigger.update(dt, player_pos, current_time, completed_tasks):
                    if trigger_id not in triggered_ids:
                        triggered_ids.append(trigger_id)
        
        return triggered_ids
    
    def trigger_interaction_near(self, player_pos: Tuple[float, float], 
                                current_floor: int, radius: float = 50.0) -> List[str]:
        """
        Déclenche les triggers d'interaction proches du joueur.
        
        Args:
            player_pos: Position du joueur
            current_floor: Étage actuel
            radius: Rayon de recherche
            
        Returns:
            Liste des IDs des triggers déclenchés
        """
        triggered_ids = []
        
        # Vérifier tous les triggers d'interaction
        all_trigger_ids = list(self.triggers.keys())
        floor_trigger_ids = self.floor_triggers.get(current_floor, [])
        
        for trigger_id in all_trigger_ids + floor_trigger_ids:
            if trigger_id in self.triggers:
                trigger = self.triggers[trigger_id]
                
                if trigger.condition.trigger_type == TriggerType.INTERACT_NEAR:
                    # Vérifier la proximité
                    near = False
                    
                    if trigger.condition.zone_rect:
                        # Étendre la zone avec le rayon
                        expanded_rect = trigger.condition.zone_rect.inflate(radius * 2, radius * 2)
                        near = point_in_rect(player_pos, expanded_rect)
                    elif trigger.condition.center_pos:
                        trigger_radius = trigger.condition.radius or radius
                        near = distance(player_pos, trigger.condition.center_pos) <= trigger_radius
                    
                    if near and trigger.trigger_interaction():
                        if trigger_id not in triggered_ids:
                            triggered_ids.append(trigger_id)
        
        return triggered_ids
    
    def get_trigger(self, trigger_id: str) -> Optional[Trigger]:
        """
        Récupère un trigger par son ID.
        
        Args:
            trigger_id: ID du trigger
            
        Returns:
            Trigger trouvé ou None
        """
        return self.triggers.get(trigger_id)
    
    def activate_trigger(self, trigger_id: str) -> bool:
        """
        Active un trigger.
        
        Args:
            trigger_id: ID du trigger
            
        Returns:
            True si le trigger a été activé
        """
        trigger = self.triggers.get(trigger_id)
        if trigger:
            trigger.activate()
            return True
        return False
    
    def deactivate_trigger(self, trigger_id: str) -> bool:
        """
        Désactive un trigger.
        
        Args:
            trigger_id: ID du trigger
            
        Returns:
            True si le trigger a été désactivé
        """
        trigger = self.triggers.get(trigger_id)
        if trigger:
            trigger.deactivate()
            return True
        return False
    
    def reset_trigger(self, trigger_id: str) -> bool:
        """
        Remet un trigger à zéro.
        
        Args:
            trigger_id: ID du trigger
            
        Returns:
            True si le trigger a été remis à zéro
        """
        trigger = self.triggers.get(trigger_id)
        if trigger:
            trigger.reset()
            return True
        return False
    
    def reset_all_triggers(self) -> None:
        """Remet tous les triggers à zéro."""
        for trigger in self.triggers.values():
            trigger.reset()
        logger.info("All triggers reset")
    
    def clear_floor_triggers(self, floor: int) -> None:
        """
        Supprime tous les triggers d'un étage.
        
        Args:
            floor: Numéro d'étage
        """
        if floor in self.floor_triggers:
            trigger_ids = self.floor_triggers[floor].copy()
            for trigger_id in trigger_ids:
                self.remove_trigger(trigger_id)
            del self.floor_triggers[floor]
            logger.debug(f"Cleared triggers for floor {floor}")
    
    def get_active_triggers(self) -> List[Trigger]:
        """
        Retourne tous les triggers actifs.
        
        Returns:
            Liste des triggers actifs
        """
        return [trigger for trigger in self.triggers.values() if trigger.active]
    
    def get_triggered_triggers(self) -> List[Trigger]:
        """
        Retourne tous les triggers déjà déclenchés.
        
        Returns:
            Liste des triggers déclenchés
        """
        return [trigger for trigger in self.triggers.values() if trigger.triggered]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur les triggers.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        total_triggers = len(self.triggers)
        active_triggers = len(self.get_active_triggers())
        triggered_triggers = len(self.get_triggered_triggers())
        
        trigger_types = {}
        for trigger in self.triggers.values():
            trigger_type = trigger.condition.trigger_type.value
            trigger_types[trigger_type] = trigger_types.get(trigger_type, 0) + 1
        
        return {
            "total_triggers": total_triggers,
            "active_triggers": active_triggers,
            "triggered_triggers": triggered_triggers,
            "floors_with_triggers": len(self.floor_triggers),
            "trigger_types": trigger_types
        }


def create_elevator_call_trigger(trigger_id: str, elevator_x: int, 
                                callback: Callable) -> Trigger:
    """
    Crée un trigger pour appeler l'ascenseur.
    
    Args:
        trigger_id: ID unique du trigger
        elevator_x: Position X de l'ascenseur
        callback: Fonction à appeler
        
    Returns:
        Trigger configuré
    """
    condition = TriggerCondition(
        trigger_type=TriggerType.INTERACT_NEAR,
        center_pos=(elevator_x, 300),  # Centre vertical approximatif
        radius=40.0
    )
    
    return Trigger(trigger_id, condition, callback, repeatable=True)


def create_task_completion_trigger(trigger_id: str, task_id: str,
                                  callback: Callable) -> Trigger:
    """
    Crée un trigger déclenché par la completion d'une tâche.
    
    Args:
        trigger_id: ID unique du trigger
        task_id: ID de la tâche à surveiller
        callback: Fonction à appeler
        
    Returns:
        Trigger configuré
    """
    condition = TriggerCondition(
        trigger_type=TriggerType.TASK_COMPLETION,
        task_id=task_id
    )
    
    return Trigger(trigger_id, condition, callback, repeatable=False)


def create_time_warning_trigger(trigger_id: str, warning_time: str,
                               callback: Callable) -> Trigger:
    """
    Crée un trigger d'avertissement temporel.
    
    Args:
        trigger_id: ID unique du trigger
        warning_time: Heure d'avertissement "HH:MM"
        callback: Fonction à appeler
        
    Returns:
        Trigger configuré
    """
    condition = TriggerCondition(
        trigger_type=TriggerType.TIME_BASED,
        time_condition=warning_time
    )
    
    return Trigger(trigger_id, condition, callback, repeatable=False)
