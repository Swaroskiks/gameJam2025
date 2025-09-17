"""
Entités du jeu : joueur, NPCs, et objets interactifs.
Gère les mouvements, collisions, et interactions.
"""

import logging
import random
from typing import Tuple, Optional, Dict, Any, List
from enum import Enum
import pygame
from src.settings import (
    PLAYER_WIDTH, PLAYER_HEIGHT, WIDTH, HEIGHT,
    WORLD_PX_PER_METER, WALK_SPEED_MPS, PLAYER_TARGET_HEIGHT_RATIO
)
from src.core.animation import AnimationManager
from src.core.utils import clamp, normalize_vector, distance

logger = logging.getLogger(__name__)


class Direction(Enum):
    """Directions possibles."""
    IDLE = "idle"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"


class Player:
    """
    Joueur contrôlable.
    """
    
    def __init__(self, x: float = 200.0, y: float = 300.0):
        self.x = x
        self.y = y
        # Vitesse exprimée en pixels/seconde (dérivée des mètres/seconde)
        self.speed = WALK_SPEED_MPS * WORLD_PX_PER_METER
        self.current_floor = 90  # Étage actuel
        
        # État du mouvement
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.direction = Direction.IDLE
        
        # Rectangle de collision
        self.rect = pygame.Rect(
            int(x - PLAYER_WIDTH // 2), 
            int(y - PLAYER_HEIGHT // 2),
            PLAYER_WIDTH, 
            PLAYER_HEIGHT
        )

        # Mise à l'échelle de rendu (ajustée par étage)
        self.render_scale: float = 1.0
        
        # Animations
        self.animation_manager = AnimationManager()
        self._setup_animations()
        
        # Statistiques
        self.distance_walked = 0.0
        self.interactions_count = 0
        
        logger.info(f"Player created at ({x}, {y})")
    
    def _setup_animations(self) -> None:
        """Configure les animations du joueur."""
        try:
            # Animation idle (statique)
            self.animation_manager.add_animation("idle", "player_idle", loop=True, auto_start=True)
            
            # Animation de marche
            self.animation_manager.add_animation("walk", "player_walk", loop=True, auto_start=False)
            
            # Définir idle comme animation par défaut
            self.animation_manager.set_default_animation("idle")
            self.animation_manager.play_animation("idle")
            
        except Exception as e:
            logger.warning(f"Could not setup player animations: {e}")
    
    def update(self, dt: float, input_vector: Tuple[float, float]) -> None:
        """
        Met à jour le joueur.
        
        Args:
            dt: Temps écoulé
            input_vector: Vecteur de mouvement (-1 à 1, -1 à 1)
        """
        # Normaliser et appliquer la vitesse
        move_x, move_y = input_vector
        
        # Limiter le mouvement horizontal uniquement (pas de saut d'étage libre)
        move_y = 0.0  # Le joueur ne peut pas monter/descendre librement
        
        if abs(move_x) > 0.1 or abs(move_y) > 0.1:
            # Normaliser le vecteur de mouvement
            normalized = normalize_vector((move_x, move_y))
            
            # Appliquer la vitesse
            self.velocity_x = normalized[0] * self.speed
            self.velocity_y = normalized[1] * self.speed
            
            # Déterminer la direction
            if abs(move_x) > abs(move_y):
                self.direction = Direction.RIGHT if move_x > 0 else Direction.LEFT
            else:
                self.direction = Direction.DOWN if move_y > 0 else Direction.UP
            
            # Jouer l'animation de marche
            self.animation_manager.play_animation("walk")
        else:
            # Arrêt
            self.velocity_x = 0.0
            self.velocity_y = 0.0
            self.direction = Direction.IDLE
            
            # Jouer l'animation idle
            self.animation_manager.play_animation("idle")
        
        # Appliquer le mouvement
        old_x, old_y = self.x, self.y
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        
        # Contraintes de mouvement (rester dans l'écran)
        self.x = clamp(self.x, PLAYER_WIDTH // 2, WIDTH - PLAYER_WIDTH // 2)
        self.y = clamp(self.y, PLAYER_HEIGHT // 2, HEIGHT - PLAYER_HEIGHT // 2)
        
        # Calculer la distance parcourue
        moved_distance = distance((old_x, old_y), (self.x, self.y))
        self.distance_walked += moved_distance
        
        # Mettre à jour le rectangle de collision
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        
        # Mettre à jour les animations
        self.animation_manager.update(dt)
    
    def set_position(self, x: float, y: float) -> None:
        """
        Définit la position du joueur.
        
        Args:
            x: Position X
            y: Position Y
        """
        self.x = x
        self.y = y
        self.rect.centerx = int(x)
        self.rect.centery = int(y)
    
    def set_floor(self, floor: int) -> None:
        """
        Définit l'étage actuel du joueur.
        
        Args:
            floor: Numéro d'étage
        """
        self.current_floor = floor
        logger.debug(f"Player moved to floor {floor}")

    def apply_floor_geometry(self, floor_geometry: Dict[str, Any], asset_manager=None) -> None:
        """
        Adapte l'échelle visuelle et la hitbox selon la géométrie de l'étage.
        
        Args:
            floor_geometry: Dictionnaire avec au minimum floor_play_height_px
            asset_manager: Optionnel, pour mesurer la hauteur sprite actuelle
        """
        try:
            play_h = int(floor_geometry.get("floor_play_height_px", 128))
            target_h = int(play_h * PLAYER_TARGET_HEIGHT_RATIO)
            # Mesurer la hauteur actuelle du sprite idle comme référence
            current_h = self.rect.height
            if asset_manager is not None:
                try:
                    sprite = asset_manager.get_image("player_idle")
                    current_h = sprite.get_height()
                except Exception:
                    pass
            # Calculer le scale de rendu et ajuster la hitbox à 90% de la hauteur
            self.render_scale = max(0.25, min(3.0, (target_h / max(1, current_h))))
            new_h = int(target_h * 0.9)
            # Conserver la largeur proportionnelle approximative
            aspect_ratio = self.rect.width / max(1, self.rect.height)
            new_w = max(16, int(new_h * aspect_ratio))
            center = self.rect.center
            self.rect.size = (new_w, new_h)
            self.rect.center = center
            # Vitesse en px/s (constante monde)
            self.speed = WALK_SPEED_MPS * WORLD_PX_PER_METER
        except Exception as e:
            logger.debug(f"apply_floor_geometry failed: {e}")
    
    def get_position(self) -> Tuple[float, float]:
        """Retourne la position actuelle."""
        return (self.x, self.y)
    
    def get_rect(self) -> pygame.Rect:
        """Retourne le rectangle de collision."""
        return self.rect
    
    def get_current_sprite(self) -> Optional[pygame.Surface]:
        """Retourne le sprite actuel du joueur."""
        return self.animation_manager.get_current_frame()
    
    def is_near_elevator(self, elevator_x: int, threshold: float = 50.0) -> bool:
        """
        Vérifie si le joueur est proche de l'ascenseur.
        
        Args:
            elevator_x: Position X de l'ascenseur
            threshold: Distance seuil
            
        Returns:
            True si proche de l'ascenseur
        """
        return abs(self.x - elevator_x) <= threshold
    
    def interact(self) -> None:
        """Enregistre une interaction."""
        self.interactions_count += 1
        logger.debug(f"Player interaction #{self.interactions_count}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du joueur.
        
        Returns:
            Dictionnaire avec les stats
        """
        return {
            "position": (self.x, self.y),
            "current_floor": self.current_floor,
            "distance_walked": self.distance_walked,
            "interactions_count": self.interactions_count,
            "direction": self.direction.value
        }


class DialogueResult:
    """Résultat d'un dialogue avec un NPC."""
    
    def __init__(self, npc_id: str, dialogue_id: str, completed: bool = True):
        self.npc_id = npc_id
        self.dialogue_id = dialogue_id
        self.completed = completed
        self.task_triggered: Optional[str] = None
        self.points_awarded = 0


class GameNPC:
    """
    NPC avec qui le joueur peut interagir dans le jeu.
    """
    
    def __init__(self, npc_id: str, name: str, x: float, y: float, dialogue_id: str, sprite_key: str = "npc_generic"):
        self.id = npc_id
        self.name = name
        self.x = x
        self.y = y
        self.dialogue_id = dialogue_id
        self.sprite_key = sprite_key
        
        # État
        self.talked_to = False
        self.conversation_count = 0
        
        # Mouvement simple (patrouille horizontale / flânerie)
        self.speed = 40.0  # pixels/seconde
        self.move_direction = 1  # 1 vers la droite, -1 vers la gauche
        self.move_min_x = x - 80
        self.move_max_x = x + 80
        self.pause_time = 0.0
        self._pick_next_pause()
        
        # Rectangle de collision
        self.rect = pygame.Rect(
            int(x - PLAYER_WIDTH // 2),
            int(y - PLAYER_HEIGHT // 2),
            PLAYER_WIDTH,
            PLAYER_HEIGHT
        )
        
        # Animation (simple pour l'instant)
        self.animation_manager = AnimationManager()
        self._setup_animations()
    
    def _setup_animations(self) -> None:
        """Configure les animations du NPC."""
        try:
            # Animation idle par défaut
            self.animation_manager.add_animation("idle", self.sprite_key, loop=True, auto_start=True)
            self.animation_manager.set_default_animation("idle")
            self.animation_manager.play_animation("idle")
        except Exception as e:
            logger.debug(f"Could not setup NPC animations for {self.id}: {e}")
    
    def _pick_next_pause(self) -> None:
        """Choisit aléatoirement une courte pause pour humaniser le mouvement."""
        # Courtes pauses occasionnelles
        self.pause_time = random.uniform(0.3, 1.2)
    
    def update(self, dt: float) -> None:
        """
        Met à jour le NPC.
        
        Args:
            dt: Temps écoulé
        """
        # Mouvement horizontal léger avec pauses
        if self.pause_time > 0.0:
            self.pause_time -= dt
        else:
            self.x += self.speed * self.move_direction * dt
            # Changement de direction aux bornes
            if self.x <= self.move_min_x:
                self.x = self.move_min_x
                self.move_direction = 1
                self._pick_next_pause()
            elif self.x >= self.move_max_x:
                self.x = self.move_max_x
                self.move_direction = -1
                self._pick_next_pause()
        
        # Mettre à jour la hitbox
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        
        # Animations (placeholder: idle loop)
        self.animation_manager.update(dt)
    
    def can_talk_to(self, player_pos: Tuple[float, float], max_distance: float = 36.0) -> bool:
        """
        Vérifie si le joueur peut parler à ce NPC.
        
        Args:
            player_pos: Position du joueur
            max_distance: Distance maximum pour l'interaction
            
        Returns:
            True si l'interaction est possible
        """
        dist = distance(player_pos, (self.x, self.y))
        return dist <= max_distance
    
    def talk(self) -> DialogueResult:
        """
        Initie une conversation avec le NPC.
        
        Returns:
            Résultat du dialogue
        """
        self.talked_to = True
        self.conversation_count += 1
        
        result = DialogueResult(self.id, self.dialogue_id)
        
        # Bonus points pour première conversation
        if self.conversation_count == 1:
            result.points_awarded = 3
        else:
            result.points_awarded = 1
        
        logger.info(f"Talked to {self.name} (conversation #{self.conversation_count})")
        return result
    
    def get_current_sprite(self) -> Optional[pygame.Surface]:
        """Retourne le sprite actuel du NPC."""
        return self.animation_manager.get_current_frame()
    
    def get_rect(self) -> pygame.Rect:
        """Retourne le rectangle de collision."""
        return self.rect


class InteractableObject:
    """
    Objet avec lequel le joueur peut interagir.
    """
    
    def __init__(self, obj_id: str, obj_type: str, x: float, y: float, task_id: Optional[str] = None):
        self.id = obj_id
        self.type = obj_type
        self.x = x
        self.y = y
        self.task_id = task_id
        
        # État
        self.interacted = False
        self.interaction_count = 0
        
        # Rectangle de collision (plus petit que les entités)
        self.rect = pygame.Rect(int(x - 16), int(y - 16), 32, 32)
        
        # Sprite (basé sur le type)
        self.sprite_key = f"interactable_{obj_type}"
    
    def can_interact_with(self, player_pos: Tuple[float, float], max_distance: float = 28.0) -> bool:
        """
        Vérifie si le joueur peut interagir avec cet objet.
        
        Args:
            player_pos: Position du joueur
            max_distance: Distance maximum pour l'interaction
            
        Returns:
            True si l'interaction est possible
        """
        if self.interacted and self.type in ["papers", "plant"]:
            # Certains objets ne peuvent être utilisés qu'une fois
            return False
        
        dist = distance(player_pos, (self.x, self.y))
        return dist <= max_distance
    
    def interact(self) -> bool:
        """
        Effectue l'interaction avec l'objet.
        
        Returns:
            True si l'interaction a réussi
        """
        if not self.can_interact_with((0, 0), float('inf')):  # Ignorer la distance pour ce test
            return False
        
        self.interacted = True
        self.interaction_count += 1
        
        logger.info(f"Interacted with {self.type} object {self.id}")
        return True
    
    def reset(self) -> None:
        """Remet l'objet dans son état initial."""
        self.interacted = False
        self.interaction_count = 0
    
    def get_sprite_key(self) -> str:
        """Retourne la clé du sprite pour cet objet."""
        return self.sprite_key
    
    def get_rect(self) -> pygame.Rect:
        """Retourne le rectangle de collision."""
        return self.rect


class EntityManager:
    """
    Gestionnaire des entités du jeu.
    """
    
    def __init__(self):
        self.player: Optional[Player] = None
        self.npcs: Dict[str, GameNPC] = {}
        self.interactables: Dict[str, InteractableObject] = {}
        
        logger.info("EntityManager initialized")
    
    def create_player(self, x: float = 200.0, y: float = 300.0) -> Player:
        """
        Crée le joueur.
        
        Args:
            x: Position X initiale
            y: Position Y initiale
            
        Returns:
            Instance du joueur créée
        """
        self.player = Player(x, y)
        return self.player
    
    def add_npc(self, npc_id: str, name: str, x: float, y: float, dialogue_id: str) -> GameNPC:
        """
        Ajoute un NPC.
        
        Args:
            npc_id: ID unique du NPC
            name: Nom du NPC
            x: Position X
            y: Position Y
            dialogue_id: ID du dialogue
            
        Returns:
            NPC créé
        """
        npc = GameNPC(npc_id, name, x, y, dialogue_id)
        self.npcs[npc_id] = npc
        return npc
    
    def add_interactable(self, obj_id: str, obj_type: str, x: float, y: float, task_id: Optional[str] = None) -> InteractableObject:
        """
        Ajoute un objet interactif.
        
        Args:
            obj_id: ID unique de l'objet
            obj_type: Type d'objet
            x: Position X
            y: Position Y
            task_id: ID de la tâche associée
            
        Returns:
            Objet créé
        """
        obj = InteractableObject(obj_id, obj_type, x, y, task_id)
        self.interactables[obj_id] = obj
        return obj
    
    def update(self, dt: float, input_vector: Tuple[float, float]) -> None:
        """
        Met à jour toutes les entités.
        
        Args:
            dt: Temps écoulé
            input_vector: Vecteur d'entrée pour le joueur
        """
        # Mettre à jour le joueur
        if self.player:
            self.player.update(dt, input_vector)
        
        # Mettre à jour les NPCs
        for npc in self.npcs.values():
            npc.update(dt)
    
    def get_nearby_interactables(self, position: Tuple[float, float], radius: float = 30.0) -> List[InteractableObject]:
        """
        Trouve les objets interactifs proches d'une position.
        
        Args:
            position: Position de référence
            radius: Rayon de recherche
            
        Returns:
            Liste des objets proches
        """
        nearby = []
        for obj in self.interactables.values():
            if obj.can_interact_with(position, radius):
                nearby.append(obj)
        return nearby
    
    def get_nearby_npcs(self, position: Tuple[float, float], radius: float = 36.0) -> List[GameNPC]:
        """
        Trouve les NPCs proches d'une position.
        
        Args:
            position: Position de référence
            radius: Rayon de recherche
            
        Returns:
            Liste des NPCs proches
        """
        nearby = []
        for npc in self.npcs.values():
            if npc.can_talk_to(position, radius):
                nearby.append(npc)
        return nearby
    
    def get_player(self) -> Optional[Player]:
        """Retourne le joueur."""
        return self.player
    
    def get_npc(self, npc_id: str) -> Optional[GameNPC]:
        """Retourne un NPC par son ID."""
        return self.npcs.get(npc_id)
    
    def get_interactable(self, obj_id: str) -> Optional[InteractableObject]:
        """Retourne un objet interactif par son ID."""
        return self.interactables.get(obj_id)
    
    def clear_floor_entities(self) -> None:
        """Vide tous les NPCs et objets de l'étage actuel."""
        self.npcs.clear()
        self.interactables.clear()
        logger.debug("Floor entities cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur les entités.
        
        Returns:
            Dictionnaire avec les stats
        """
        return {
            "player_exists": self.player is not None,
            "npc_count": len(self.npcs),
            "interactable_count": len(self.interactables),
            "total_conversations": sum(npc.conversation_count for npc in self.npcs.values()),
            "total_interactions": sum(obj.interaction_count for obj in self.interactables.values())
        }
