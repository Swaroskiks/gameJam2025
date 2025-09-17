"""
Système de caméra avec lissage pour A Day at the Office.
Gère le défilement fluide lors des déplacements d'étage.
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class Camera:
    """
    Caméra verticale avec lissage pour le défilement d'étages.
    
    Gère l'interpolation fluide entre les positions pour éviter
    l'effet de "rester sur place" lors des déplacements d'ascenseur.
    """
    
    def __init__(self, initial_y: float = 500.0, speed: float = 200.0):
        """
        Initialise la caméra.
        
        Args:
            initial_y: Position Y initiale
            speed: Vitesse d'interpolation en pixels/seconde
        """
        self.y = initial_y
        self.target_y = initial_y
        self.speed = speed
        self.is_moving = False
        
        logger.debug(f"Camera initialized at y={initial_y}, speed={speed}")
    
    def set_target(self, target_y: float) -> None:
        """
        Définit la position cible de la caméra.
        
        Args:
            target_y: Position Y cible
        """
        if abs(target_y - self.target_y) > 1.0:  # Éviter les micro-ajustements
            self.target_y = target_y
            self.is_moving = True
            logger.debug(f"Camera target set to y={target_y}")
    
    def update(self, dt: float) -> None:
        """
        Met à jour la position de la caméra avec interpolation.
        
        Args:
            dt: Temps écoulé depuis la dernière frame en secondes
        """
        if not self.is_moving:
            return
        
        # Distance à parcourir
        distance = self.target_y - self.y
        
        # Vérifier si on est arrivé (seuil de 1 pixel)
        if abs(distance) <= 1.0:
            self.y = self.target_y
            self.is_moving = False
            logger.debug(f"Camera reached target y={self.target_y}")
            return
        
        # Interpolation linéaire avec vitesse constante
        move_distance = self.speed * dt
        if abs(distance) < move_distance:
            # Éviter le dépassement
            self.y = self.target_y
            self.is_moving = False
            logger.debug(f"Camera reached target y={self.target_y}")
        else:
            # Déplacement vers la cible
            direction = 1.0 if distance > 0 else -1.0
            self.y += move_distance * direction
    
    def get_offset(self) -> Tuple[float, float]:
        """
        Retourne l'offset de la caméra pour le rendu.
        
        Returns:
            Tuple (offset_x, offset_y) - offset_x toujours 0 pour cette caméra verticale
        """
        return (0.0, -self.y)
    
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """
        Convertit des coordonnées monde en coordonnées écran.
        
        Args:
            world_x: Position X dans le monde
            world_y: Position Y dans le monde
            
        Returns:
            Tuple (screen_x, screen_y)
        """
        offset_x, offset_y = self.get_offset()
        return (world_x + offset_x, world_y + offset_y)
    
    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """
        Convertit des coordonnées écran en coordonnées monde.
        
        Args:
            screen_x: Position X à l'écran
            screen_y: Position Y à l'écran
            
        Returns:
            Tuple (world_x, world_y)
        """
        offset_x, offset_y = self.get_offset()
        return (screen_x - offset_x, screen_y - offset_y)
    
    def is_at_target(self) -> bool:
        """
        Vérifie si la caméra a atteint sa position cible.
        
        Returns:
            True si la caméra est à sa position cible
        """
        return not self.is_moving
    
    def snap_to_target(self) -> None:
        """Force la caméra à sa position cible immédiatement."""
        self.y = self.target_y
        self.is_moving = False
        logger.debug(f"Camera snapped to target y={self.target_y}")
    
    def get_position(self) -> float:
        """
        Retourne la position Y actuelle de la caméra.
        
        Returns:
            Position Y actuelle
        """
        return self.y
    
    def get_target(self) -> float:
        """
        Retourne la position Y cible de la caméra.
        
        Returns:
            Position Y cible
        """
        return self.target_y
