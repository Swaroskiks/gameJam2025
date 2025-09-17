"""
Système de déplacement des NPCs pour A Day at the Office.
Gère le mouvement semi-aléatoire des NPCs avec évitement des collisions.
"""

import logging
import random
import math
from typing import List, Dict, Tuple, Optional
import pygame

logger = logging.getLogger(__name__)


class NPCMovement:
    """Gestionnaire de mouvement pour un NPC."""
    
    def __init__(self, npc, floor_width: int = 1000, movement_speed: float = 20.0):
        self.npc = npc
        self.floor_width = floor_width
        self.movement_speed = movement_speed
        
        # État du mouvement
        self.target_x = npc.x
        self.moving = False
        self.idle_timer = 0.0
        self.idle_duration = random.uniform(2.0, 8.0)  # Temps d'arrêt aléatoire
        
        # Paramètres de mouvement
        self.min_x = 150  # Éviter l'ascenseur
        self.max_x = floor_width - 100  # Éviter les bords
        
        logger.debug(f"NPCMovement initialized for {getattr(npc, 'name', 'Unknown')}")
    
    def update(self, dt: float, other_npcs: List) -> None:
        """Met à jour le mouvement du NPC."""
        if not self.moving:
            self.idle_timer += dt
            
            # Vérifier si on doit commencer à bouger
            if self.idle_timer >= self.idle_duration:
                self._choose_new_target(other_npcs)
                self.moving = True
                self.idle_timer = 0.0
        else:
            # Se déplacer vers la cible
            self._move_towards_target(dt, other_npcs)
    
    def _choose_new_target(self, other_npcs: List) -> None:
        """Choisit une nouvelle position cible."""
        attempts = 0
        max_attempts = 10
        
        while attempts < max_attempts:
            # Position aléatoire dans la zone autorisée
            new_target = random.uniform(self.min_x, self.max_x)
            
            # Vérifier qu'on n'est pas trop proche d'autres NPCs
            too_close = False
            for other_npc in other_npcs:
                if other_npc != self.npc and hasattr(other_npc, 'x'):
                    distance = abs(new_target - other_npc.x)
                    if distance < 80:  # Distance minimale entre NPCs
                        too_close = True
                        break
            
            if not too_close:
                self.target_x = new_target
                self.idle_duration = random.uniform(3.0, 10.0)  # Nouveau temps d'arrêt
                logger.debug(f"New target chosen: {self.target_x:.1f}")
                return
            
            attempts += 1
        
        # Si on n'a pas trouvé de bonne position, rester sur place
        self.target_x = self.npc.x
        self.idle_duration = random.uniform(1.0, 3.0)
    
    def _move_towards_target(self, dt: float, other_npcs: List) -> None:
        """Se déplace vers la cible en évitant les collisions."""
        distance_to_target = abs(self.target_x - self.npc.x)
        
        if distance_to_target < 5:  # Arrivé à destination
            self.npc.x = self.target_x
            self.moving = False
            return
        
        # Calculer la direction de mouvement
        direction = 1 if self.target_x > self.npc.x else -1
        
        # Calculer la distance de mouvement
        move_distance = self.movement_speed * dt
        
        # Vérifier les collisions avec d'autres NPCs
        new_x = self.npc.x + (direction * move_distance)
        
        # Éviter les collisions
        for other_npc in other_npcs:
            if other_npc != self.npc and hasattr(other_npc, 'x'):
                distance = abs(new_x - other_npc.x)
                if distance < 60:  # Zone de collision
                    # S'arrêter ou changer de direction
                    self.moving = False
                    self.idle_duration = random.uniform(1.0, 3.0)
                    return
        
        # Appliquer le mouvement
        self.npc.x = new_x
        
        # S'assurer qu'on reste dans les limites
        self.npc.x = max(self.min_x, min(self.max_x, self.npc.x))


class NPCMovementManager:
    """Gestionnaire global du mouvement des NPCs."""
    
    def __init__(self):
        self.npc_movements: Dict[str, NPCMovement] = {}
        self.fixed_npcs = {
            "boss_reed",  # Le boss reste à son bureau
            "receptionist_95",  # La réceptionniste reste à l'accueil
        }
        self.static_npcs: Dict[str, object] = {}  # Registre des PNJ fixes pour le rendu
        
        logger.info("NPCMovementManager initialized")
    
    def add_npc(self, npc, floor_width: int = 1000) -> None:
        """Ajoute un NPC au système de mouvement."""
        npc_id = getattr(npc, 'id', f"npc_{id(npc)}")
        
        # Vérifier si le NPC doit être fixe
        if npc_id in self.fixed_npcs:
            # Garder une référence pour le rendu & l'ancre bulle
            self.static_npcs[npc_id] = npc
            logger.debug(f"NPC {npc_id} registered as STATIC")
            return
        
        # Créer le gestionnaire de mouvement
        movement_speed = random.uniform(15.0, 35.0)  # Vitesse variable
        movement = NPCMovement(npc, floor_width, movement_speed)
        self.npc_movements[npc_id] = movement
        
        logger.debug(f"NPC {npc_id} added to movement system")
    
    def remove_npc(self, npc) -> None:
        """Retire un NPC du système de mouvement."""
        npc_id = getattr(npc, 'id', f"npc_{id(npc)}")
        if npc_id in self.npc_movements:
            del self.npc_movements[npc_id]
            logger.debug(f"NPC {npc_id} removed from movement system")
    
    def update(self, dt: float) -> None:
        """Met à jour le mouvement de tous les NPCs."""
        # Grouper les NPCs par étage pour éviter les collisions inter-étages
        npcs_by_floor = {}
        
        for movement in self.npc_movements.values():
            npc = movement.npc
            floor = getattr(npc, 'current_floor', 90)
            
            if floor not in npcs_by_floor:
                npcs_by_floor[floor] = []
            npcs_by_floor[floor].append(npc)
        
        # Mettre à jour chaque étage séparément
        for floor, npcs in npcs_by_floor.items():
            for movement in self.npc_movements.values():
                if movement.npc in npcs:
                    movement.update(dt, npcs)
    
    def get_npc_position(self, npc) -> Tuple[float, float]:
        """Récupère la position actuelle d'un NPC."""
        if hasattr(npc, 'x') and hasattr(npc, 'y'):
            return (npc.x, npc.y)
        return (0, 0)
    
    def set_npc_position(self, npc, x: float, y: float) -> None:
        """Définit la position d'un NPC."""
        if hasattr(npc, 'x'):
            npc.x = x
        if hasattr(npc, 'y'):
            npc.y = y
