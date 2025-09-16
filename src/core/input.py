"""
Gestionnaire d'entrées centralisé pour A Day at the Office.
Gère les entrées clavier et souris avec mapping configurable.
"""

import logging
from typing import Dict, Set, Optional, Callable, Any
from enum import Enum
import pygame

logger = logging.getLogger(__name__)


class InputAction(Enum):
    """Actions d'entrée du jeu."""
    
    # Mouvement
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    
    # Actions
    INTERACT = "interact"
    
    # Ascenseur
    ELEVATOR_CALL = "elevator_call"
    ELEVATOR_UP = "elevator_up"
    ELEVATOR_DOWN = "elevator_down"
    
    # Interface
    PAUSE = "pause"
    MENU = "menu"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    
    # Debug (dev mode)
    DEBUG_TOGGLE = "debug_toggle"
    RELOAD_ASSETS = "reload_assets"
    
    # Sélection d'étage (chiffres)
    FLOOR_0 = "floor_0"
    FLOOR_1 = "floor_1"
    FLOOR_2 = "floor_2"
    FLOOR_3 = "floor_3"
    FLOOR_4 = "floor_4"
    FLOOR_5 = "floor_5"
    FLOOR_6 = "floor_6"
    FLOOR_7 = "floor_7"
    FLOOR_8 = "floor_8"
    FLOOR_9 = "floor_9"


class InputManager:
    """
    Gestionnaire d'entrées centralisé.
    
    Permet de mapper les touches aux actions, gérer les états pressed/held/released,
    et fournir une interface uniforme pour les contrôles.
    """
    
    def __init__(self):
        # Mapping par défaut des touches
        self.key_mapping: Dict[int, InputAction] = {
            # Mouvement
            pygame.K_LEFT: InputAction.MOVE_LEFT,
            pygame.K_a: InputAction.MOVE_LEFT,
            pygame.K_RIGHT: InputAction.MOVE_RIGHT,
            pygame.K_d: InputAction.MOVE_RIGHT,
            pygame.K_UP: InputAction.MOVE_UP,
            pygame.K_w: InputAction.MOVE_UP,
            pygame.K_DOWN: InputAction.MOVE_DOWN,
            pygame.K_s: InputAction.MOVE_DOWN,
            
            # Actions
            pygame.K_e: InputAction.INTERACT,
            pygame.K_SPACE: InputAction.INTERACT,
            pygame.K_RETURN: InputAction.INTERACT,
            
            # Ascenseur
            pygame.K_UP: InputAction.ELEVATOR_UP,
            pygame.K_DOWN: InputAction.ELEVATOR_DOWN,
            pygame.K_c: InputAction.ELEVATOR_CALL,
            
            # Interface
            pygame.K_ESCAPE: InputAction.PAUSE,
            pygame.K_p: InputAction.PAUSE,
            pygame.K_RETURN: InputAction.CONFIRM,
            pygame.K_ESCAPE: InputAction.CANCEL,
            
            # Debug
            pygame.K_F1: InputAction.DEBUG_TOGGLE,
            pygame.K_F5: InputAction.RELOAD_ASSETS,
            
            # Chiffres pour étages (mapper vers 90-99)
            pygame.K_0: InputAction.FLOOR_0,
            pygame.K_1: InputAction.FLOOR_1,
            pygame.K_2: InputAction.FLOOR_2,
            pygame.K_3: InputAction.FLOOR_3,
            pygame.K_4: InputAction.FLOOR_4,
            pygame.K_5: InputAction.FLOOR_5,
            pygame.K_6: InputAction.FLOOR_6,
            pygame.K_7: InputAction.FLOOR_7,
            pygame.K_8: InputAction.FLOOR_8,
            pygame.K_9: InputAction.FLOOR_9,
        }
        
        # États des actions
        self.actions_pressed: Set[InputAction] = set()  # Enfoncées cette frame
        self.actions_held: Set[InputAction] = set()     # Maintenues
        self.actions_released: Set[InputAction] = set() # Relâchées cette frame
        
        # Position de la souris
        self.mouse_pos = (0, 0)
        self.mouse_pressed: Set[int] = set()
        self.mouse_held: Set[int] = set()
        self.mouse_released: Set[int] = set()
        
        # Callbacks pour les actions
        self.action_callbacks: Dict[InputAction, list[Callable]] = {}
        
        logger.info("InputManager initialized")
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Traite un événement pygame.
        
        Args:
            event: Événement pygame à traiter
        """
        if event.type == pygame.KEYDOWN:
            action = self.key_mapping.get(event.key)
            if action:
                self.actions_pressed.add(action)
                self.actions_held.add(action)
                self._trigger_callbacks(action, True)
        
        elif event.type == pygame.KEYUP:
            action = self.key_mapping.get(event.key)
            if action:
                self.actions_released.add(action)
                self.actions_held.discard(action)
                self._trigger_callbacks(action, False)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_pressed.add(event.button)
            self.mouse_held.add(event.button)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            self.mouse_released.add(event.button)
            self.mouse_held.discard(event.button)
        
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
    
    def update(self) -> None:
        """Met à jour les états (à appeler chaque frame)."""
        # Vider les états "cette frame"
        self.actions_pressed.clear()
        self.actions_released.clear()
        self.mouse_pressed.clear()
        self.mouse_released.clear()
    
    def is_action_pressed(self, action: InputAction) -> bool:
        """
        Vérifie si une action a été enfoncée cette frame.
        
        Args:
            action: Action à vérifier
            
        Returns:
            True si l'action a été enfoncée cette frame
        """
        return action in self.actions_pressed
    
    def is_action_held(self, action: InputAction) -> bool:
        """
        Vérifie si une action est maintenue.
        
        Args:
            action: Action à vérifier
            
        Returns:
            True si l'action est maintenue
        """
        return action in self.actions_held
    
    def is_action_released(self, action: InputAction) -> bool:
        """
        Vérifie si une action a été relâchée cette frame.
        
        Args:
            action: Action à vérifier
            
        Returns:
            True si l'action a été relâchée cette frame
        """
        return action in self.actions_released
    
    def get_movement_vector(self) -> tuple[float, float]:
        """
        Retourne le vecteur de mouvement basé sur les entrées.
        
        Returns:
            Tuple (x, y) normalisé entre -1 et 1
        """
        x = 0.0
        y = 0.0
        
        if self.is_action_held(InputAction.MOVE_LEFT):
            x -= 1.0
        if self.is_action_held(InputAction.MOVE_RIGHT):
            x += 1.0
        if self.is_action_held(InputAction.MOVE_UP):
            y -= 1.0
        if self.is_action_held(InputAction.MOVE_DOWN):
            y += 1.0
        
        return (x, y)
    
    def get_floor_from_number_key(self) -> Optional[int]:
        """
        Retourne l'étage correspondant à la touche chiffre pressée.
        Mappe 0-9 vers les étages 90-99.
        
        Returns:
            Numéro d'étage ou None si aucune touche chiffre pressée
        """
        for i in range(10):
            action = InputAction(f"floor_{i}")
            if self.is_action_pressed(action):
                return 90 + i
        return None
    
    def is_mouse_pressed(self, button: int = 1) -> bool:
        """
        Vérifie si un bouton de souris a été enfoncé cette frame.
        
        Args:
            button: Numéro du bouton (1=gauche, 2=milieu, 3=droite)
            
        Returns:
            True si le bouton a été enfoncé cette frame
        """
        return button in self.mouse_pressed
    
    def is_mouse_held(self, button: int = 1) -> bool:
        """
        Vérifie si un bouton de souris est maintenu.
        
        Args:
            button: Numéro du bouton
            
        Returns:
            True si le bouton est maintenu
        """
        return button in self.mouse_held
    
    def get_mouse_pos(self) -> tuple[int, int]:
        """Retourne la position actuelle de la souris."""
        return self.mouse_pos
    
    def register_callback(self, action: InputAction, callback: Callable[[bool], None]) -> None:
        """
        Enregistre un callback pour une action.
        
        Args:
            action: Action à surveiller
            callback: Fonction à appeler (reçoit True pour press, False pour release)
        """
        if action not in self.action_callbacks:
            self.action_callbacks[action] = []
        self.action_callbacks[action].append(callback)
    
    def unregister_callback(self, action: InputAction, callback: Callable) -> None:
        """
        Désenregistre un callback.
        
        Args:
            action: Action concernée
            callback: Fonction à retirer
        """
        if action in self.action_callbacks:
            try:
                self.action_callbacks[action].remove(callback)
            except ValueError:
                pass
    
    def _trigger_callbacks(self, action: InputAction, pressed: bool) -> None:
        """
        Déclenche les callbacks pour une action.
        
        Args:
            action: Action déclenchée
            pressed: True si enfoncée, False si relâchée
        """
        if action in self.action_callbacks:
            for callback in self.action_callbacks[action]:
                try:
                    callback(pressed)
                except Exception as e:
                    logger.error(f"Error in input callback: {e}")
    
    def remap_key(self, key: int, action: InputAction) -> None:
        """
        Remapper une touche vers une action.
        
        Args:
            key: Code de la touche pygame
            action: Action à associer
        """
        self.key_mapping[key] = action
        logger.debug(f"Remapped key {key} to {action}")
    
    def clear_mapping(self) -> None:
        """Vide tous les mappings de touches."""
        self.key_mapping.clear()
        logger.info("Key mappings cleared")
    
    def get_mapped_keys(self, action: InputAction) -> list[int]:
        """
        Retourne les touches mappées pour une action.
        
        Args:
            action: Action à chercher
            
        Returns:
            Liste des codes de touches
        """
        return [key for key, mapped_action in self.key_mapping.items() if mapped_action == action]
