"""
Gestionnaire de scènes pour A Day at the Office.
Permet de basculer entre menu, gameplay, pause, summary, etc.
"""

import logging
from typing import Dict, Any, Optional, Type
from abc import ABC, abstractmethod
import pygame

logger = logging.getLogger(__name__)


class Scene(ABC):
    """
    Classe de base pour toutes les scènes du jeu.
    """
    
    def __init__(self, scene_manager: 'SceneManager'):
        self.scene_manager = scene_manager
        self.is_active = False
        self.transition_data: Dict[str, Any] = {}
    
    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Gère un événement pygame.
        
        Args:
            event: Événement pygame à traiter
        """
        pass
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Met à jour la logique de la scène.
        
        Args:
            dt: Temps écoulé depuis la dernière frame (en secondes)
        """
        pass
    
    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """
        Dessine la scène sur l'écran.
        
        Args:
            screen: Surface pygame sur laquelle dessiner
        """
        pass
    
    def enter(self, **kwargs) -> None:
        """
        Appelé quand on entre dans cette scène.
        
        Args:
            **kwargs: Données de transition passées par switch_scene()
        """
        self.is_active = True
        self.transition_data = kwargs
        logger.debug(f"Entered scene: {self.__class__.__name__}")
    
    def exit(self) -> None:
        """Appelé quand on quitte cette scène."""
        self.is_active = False
        self.transition_data.clear()
        logger.debug(f"Exited scene: {self.__class__.__name__}")
    
    def switch_to(self, scene_name: str, **kwargs) -> None:
        """
        Raccourci pour changer de scène depuis cette scène.
        
        Args:
            scene_name: Nom de la scène de destination
            **kwargs: Données à passer à la nouvelle scène
        """
        self.scene_manager.switch_scene(scene_name, **kwargs)


class SceneManager:
    """
    Gestionnaire central des scènes du jeu.
    """
    
    def __init__(self):
        self.scenes: Dict[str, Scene] = {}
        self.current_scene: Optional[Scene] = None
        self.scene_stack: list[str] = []  # Pour gérer pause/resume
        
    def register_scene(self, name: str, scene_class: Type[Scene]) -> None:
        """
        Enregistre une classe de scène.
        
        Args:
            name: Nom unique de la scène
            scene_class: Classe héritant de Scene
        """
        if name in self.scenes:
            logger.warning(f"Scene '{name}' already registered, replacing")
        
        # Instancier la scène
        scene_instance = scene_class(self)
        self.scenes[name] = scene_instance
        logger.info(f"Scene registered: {name}")
    
    def switch_scene(self, name: str, **kwargs) -> bool:
        """
        Bascule vers une nouvelle scène.
        
        Args:
            name: Nom de la scène de destination
            **kwargs: Données à passer à la nouvelle scène
            
        Returns:
            True si le changement a réussi
        """
        if name not in self.scenes:
            logger.error(f"Scene '{name}' not found")
            return False
        
        # Quitter la scène actuelle
        if self.current_scene:
            self.current_scene.exit()
        
        # Entrer dans la nouvelle scène
        new_scene = self.scenes[name]
        new_scene.enter(**kwargs)
        self.current_scene = new_scene
        
        logger.info(f"Switched to scene: {name}")
        return True
    
    def push_scene(self, name: str, **kwargs) -> bool:
        """
        Pousse une nouvelle scène sur la pile (pour pause/modal).
        
        Args:
            name: Nom de la scène à pousser
            **kwargs: Données à passer à la nouvelle scène
            
        Returns:
            True si l'opération a réussi
        """
        if name not in self.scenes:
            logger.error(f"Scene '{name}' not found")
            return False
        
        # Sauvegarder la scène actuelle dans la pile
        if self.current_scene:
            current_name = self._get_scene_name(self.current_scene)
            if current_name:
                self.scene_stack.append(current_name)
                self.current_scene.exit()
        
        # Activer la nouvelle scène
        new_scene = self.scenes[name]
        new_scene.enter(**kwargs)
        self.current_scene = new_scene
        
        logger.info(f"Pushed scene: {name}")
        return True
    
    def pop_scene(self) -> bool:
        """
        Retire la scène actuelle et revient à la précédente.
        
        Returns:
            True si l'opération a réussi
        """
        if not self.scene_stack:
            logger.warning("No scene to pop to")
            return False
        
        # Quitter la scène actuelle
        if self.current_scene:
            self.current_scene.exit()
        
        # Revenir à la scène précédente
        previous_name = self.scene_stack.pop()
        previous_scene = self.scenes[previous_name]
        previous_scene.enter()
        self.current_scene = previous_scene
        
        logger.info(f"Popped to scene: {previous_name}")
        return True
    
    def _get_scene_name(self, scene: Scene) -> Optional[str]:
        """
        Trouve le nom d'une instance de scène.
        
        Args:
            scene: Instance de scène
            
        Returns:
            Nom de la scène ou None si non trouvée
        """
        for name, registered_scene in self.scenes.items():
            if registered_scene is scene:
                return name
        return None
    
    def get_current_scene(self) -> Optional[Scene]:
        """Retourne la scène actuellement active."""
        return self.current_scene
    
    def get_current_scene_name(self) -> Optional[str]:
        """Retourne le nom de la scène actuellement active."""
        if self.current_scene:
            return self._get_scene_name(self.current_scene)
        return None
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Transmet un événement à la scène actuelle.
        
        Args:
            event: Événement pygame
        """
        if self.current_scene:
            self.current_scene.handle_event(event)
    
    def update(self, dt: float) -> None:
        """
        Met à jour la scène actuelle.
        
        Args:
            dt: Temps écoulé depuis la dernière frame
        """
        if self.current_scene:
            self.current_scene.update(dt)
    
    def draw(self, screen: pygame.Surface) -> None:
        """
        Dessine la scène actuelle.
        
        Args:
            screen: Surface pygame sur laquelle dessiner
        """
        if self.current_scene:
            self.current_scene.draw(screen)
    
    def has_scene(self, name: str) -> bool:
        """
        Vérifie si une scène est enregistrée.
        
        Args:
            name: Nom de la scène
            
        Returns:
            True si la scène existe
        """
        return name in self.scenes
    
    def list_scenes(self) -> list[str]:
        """Retourne la liste des noms de scènes enregistrées."""
        return list(self.scenes.keys())
    
    def clear_stack(self) -> None:
        """Vide la pile de scènes."""
        self.scene_stack.clear()
        logger.debug("Scene stack cleared")
