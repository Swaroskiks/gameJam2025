"""
Gestion du bâtiment et des étages pour A Day at the Office.
Vue de coupe avec rendu contextuel des étages visibles.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import pygame
from src.settings import VISIBLE_FLOOR_RADIUS, MIN_FLOOR, MAX_FLOOR
from src.core.utils import load_json_safe, safe_get

logger = logging.getLogger(__name__)


class Floor:
    """
    Représente un étage du bâtiment.
    """
    
    def __init__(self, floor_number: int, floor_data: Dict[str, Any]):
        self.number = floor_number
        self.name = safe_get(floor_data, "name", f"Étage {floor_number}")
        self.rooms = safe_get(floor_data, "rooms", [])
        
        # Support des fonds d'étage personnalisés
        self.bg_key = safe_get(floor_data, "bg_key", None)
        self.background_surface = None  # Sera chargé par le world_loader
        
        # Géométrie et contraintes d'échelle
        self.geometry: Dict[str, Any] = safe_get(floor_data, "geometry", {}) or {}
        if "floor_play_height_px" not in self.geometry:
            self.geometry["floor_play_height_px"] = 128
        if "walkline_y" not in self.geometry:
            self.geometry["walkline_y"] = 24
        if "elevator" not in self.geometry:
            self.geometry["elevator"] = {"x": 64, "door_w": 64, "door_h": 96}

        # Listes d'objets (nouveau système)
        self.objects = []
        self.interactables = []  # Conservé pour compatibilité
        self.npcs = []  # Conservé pour compatibilité
        
        # Charger les objets (nouveau système objects[])
        objects_data = safe_get(floor_data, "objects", [])
        for obj_data in objects_data:
            if isinstance(obj_data, dict):
                self.objects.append(obj_data)
        
        # Support de l'ancien format (compatibilité)
        interactables_data = safe_get(floor_data, "interactables", [])
        for item_data in interactables_data:
            if isinstance(item_data, dict):
                self.interactables.append(Interactable(item_data))
        
        npcs_data = safe_get(floor_data, "npcs", [])
        for npc_data in npcs_data:
            if isinstance(npc_data, dict):
                self.npcs.append(NPC(npc_data))
        
        logger.debug(f"Floor {floor_number} created: {len(self.objects)} objects, {len(self.interactables)} legacy interactables, {len(self.npcs)} legacy NPCs")
    
    def load_background(self, asset_manager, default_bg_key: Optional[str] = None) -> None:
        """
        Charge le fond d'étage depuis l'AssetManager.
        
        Args:
            asset_manager: Gestionnaire d'assets
            default_bg_key: Clé de fond par défaut si bg_key n'est pas défini
        """
        bg_key = self.bg_key or default_bg_key
        if bg_key:
            try:
                # Utiliser get_background si disponible, sinon get_image
                if hasattr(asset_manager, 'get_background'):
                    self.background_surface = asset_manager.get_background(bg_key)
                else:
                    self.background_surface = asset_manager.get_image(bg_key)
                logger.debug(f"Floor {self.number} background loaded: {bg_key}")
            except Exception as e:
                logger.error(f"Failed to load background {bg_key} for floor {self.number}: {e}")
                self.background_surface = None
        else:
            logger.debug(f"Floor {self.number} has no background key")
            self.background_surface = None
    
    def get_interactable(self, interactable_id: str) -> Optional['Interactable']:
        """
        Trouve un interactable par son ID.
        
        Args:
            interactable_id: ID de l'interactable
            
        Returns:
            Interactable trouvé ou None
        """
        for interactable in self.interactables:
            if interactable.id == interactable_id:
                return interactable
        return None
    
    def get_npc(self, npc_id: str) -> Optional['NPC']:
        """
        Trouve un NPC par son ID.
        
        Args:
            npc_id: ID du NPC
            
        Returns:
            NPC trouvé ou None
        """
        for npc in self.npcs:
            if npc.id == npc_id:
                return npc
        return None
    
    def get_interactables_near(self, pos: Tuple[float, float], radius: float = 50.0) -> List['Interactable']:
        """
        Retourne les interactables proches d'une position.
        
        Args:
            pos: Position (x, y)
            radius: Rayon de recherche
            
        Returns:
            Liste des interactables dans le rayon
        """
        nearby = []
        for interactable in self.interactables:
            distance = ((pos[0] - interactable.x) ** 2 + (pos[1] - interactable.y) ** 2) ** 0.5
            if distance <= radius:
                nearby.append(interactable)
        return nearby
    
    def get_npcs_near(self, pos: Tuple[float, float], radius: float = 50.0) -> List['NPC']:
        """
        Retourne les NPCs proches d'une position.
        
        Args:
            pos: Position (x, y)
            radius: Rayon de recherche
            
        Returns:
            Liste des NPCs dans le rayon
        """
        nearby = []
        for npc in self.npcs:
            distance = ((pos[0] - npc.x) ** 2 + (pos[1] - npc.y) ** 2) ** 0.5
            if distance <= radius:
                nearby.append(npc)
        return nearby


class Interactable:
    """
    Objet avec lequel le joueur peut interagir.
    """
    
    def __init__(self, data: Dict[str, Any]):
        self.id = safe_get(data, "id", "unknown")
        self.type = safe_get(data, "type", "generic")
        self.x = safe_get(data, "x", 0)
        self.y = safe_get(data, "y", 0)
        self.task_id = safe_get(data, "task_id")
        self.interacted = False
        
        # Rectangle de collision (par défaut 32x32)
        self.rect = pygame.Rect(self.x - 16, self.y - 16, 32, 32)
    
    def can_interact(self) -> bool:
        """
        Vérifie si l'objet peut être utilisé.
        
        Returns:
            True si l'interaction est possible
        """
        return not self.interacted
    
    def interact(self) -> bool:
        """
        Effectue l'interaction.
        
        Returns:
            True si l'interaction a réussi
        """
        if self.can_interact():
            self.interacted = True
            logger.info(f"Interacted with {self.id}")
            return True
        return False
    
    def reset(self) -> None:
        """Remet l'interactable dans son état initial."""
        self.interacted = False


class NPC:
    """
    Personnage non-joueur.
    """
    
    def __init__(self, data: Dict[str, Any]):
        self.id = safe_get(data, "id", "unknown")
        self.name = safe_get(data, "name", "Inconnu")
        self.x = safe_get(data, "x", 0)
        self.y = safe_get(data, "y", 0)
        self.dialogue_id = safe_get(data, "dialogue_id")
        self.talked_to = False
        
        # Rectangle de collision
        self.rect = pygame.Rect(self.x - 16, self.y - 24, 32, 48)
    
    def can_talk(self) -> bool:
        """
        Vérifie si on peut parler au NPC.
        
        Returns:
            True si la conversation est possible
        """
        return True  # On peut toujours reparler aux NPCs
    
    def talk(self) -> bool:
        """
        Initie une conversation.
        
        Returns:
            True si la conversation a commencé
        """
        if self.can_talk():
            self.talked_to = True
            logger.info(f"Talked to {self.name}")
            return True
        return False


class Building:
    """
    Représente le bâtiment entier avec tous ses étages.
    Gère le rendu contextuel et la navigation.
    """
    
    def __init__(self):
        self.floors: Dict[int, Floor] = {}
        self.elevator_x = 64  # Position X de l'ascenseur
        self.floor_height = 120  # Hauteur d'un étage en pixels
        
        # Limites du bâtiment
        self.min_floor = 90
        self.max_floor = 98
        
        # Statistiques
        self.floors_visited: set[int] = set()
        
        logger.info("Building initialized")
    
    def load_from_data(self, floors_data: Dict[str, Any]) -> bool:
        """
        Charge la configuration des étages depuis les données JSON.
        
        Args:
            floors_data: Données des étages depuis floors.json
            
        Returns:
            True si le chargement a réussi
        """
        try:
            # Paramètres globaux
            self.elevator_x = safe_get(floors_data, "elevator_position_x", 64)
            self.floor_height = safe_get(floors_data, "floor_height", 120)
            self.min_floor = safe_get(floors_data, "min_floor", 90)
            self.max_floor = safe_get(floors_data, "max_floor", 98)
            
            # Charger chaque étage
            floors_config = safe_get(floors_data, "floors", {})
            
            for floor_str, floor_data in floors_config.items():
                try:
                    floor_number = int(floor_str)
                    if self.min_floor <= floor_number <= self.max_floor:
                        self.floors[floor_number] = Floor(floor_number, floor_data)
                    else:
                        logger.warning(f"Floor {floor_number} outside valid range {self.min_floor}-{self.max_floor}")
                except ValueError:
                    logger.error(f"Invalid floor number: {floor_str}")
            
            logger.info(f"Building loaded: {len(self.floors)} floors")
            return True
            
        except Exception as e:
            logger.error(f"Error loading building data: {e}")
            return False
    
    def get_floor(self, floor_number: int) -> Optional[Floor]:
        """
        Récupère un étage par son numéro.
        
        Args:
            floor_number: Numéro de l'étage
            
        Returns:
            Étage trouvé ou None
        """
        return self.floors.get(floor_number)
    
    def has_floor(self, floor_number: int) -> bool:
        """
        Vérifie si un étage existe.
        
        Args:
            floor_number: Numéro de l'étage
            
        Returns:
            True si l'étage existe
        """
        return floor_number in self.floors
    
    def get_visible_floors(self, center_floor: int, radius: Optional[int] = None) -> List[int]:
        """
        Retourne les étages visibles autour d'un étage central.
        
        Args:
            center_floor: Étage central
            radius: Rayon de visibilité (défaut: VISIBLE_FLOOR_RADIUS)
            
        Returns:
            Liste des numéros d'étages visibles, triés
        """
        if radius is None:
            radius = VISIBLE_FLOOR_RADIUS
        
        visible = []
        for floor_num in self.floors.keys():
            if abs(floor_num - center_floor) <= radius:
                visible.append(floor_num)
        
        return sorted(visible)
    
    def get_floor_y_position(self, floor_number: int, camera_floor: int) -> int:
        """
        Calcule la position Y d'un étage à l'écran.
        
        Args:
            floor_number: Numéro de l'étage à positionner
            camera_floor: Étage de référence de la caméra
            
        Returns:
            Position Y en pixels
        """
        # Les étages plus hauts sont plus haut à l'écran (Y plus petit)
        floor_offset = camera_floor - floor_number
        return 300 + (floor_offset * self.floor_height)  # 300 = centre écran approximatif
    
    def visit_floor(self, floor_number: int) -> None:
        """
        Marque un étage comme visité.
        
        Args:
            floor_number: Numéro de l'étage visité
        """
        if self.has_floor(floor_number):
            self.floors_visited.add(floor_number)
            logger.debug(f"Floor {floor_number} visited")
    
    def get_visited_floors_count(self) -> int:
        """Retourne le nombre d'étages visités."""
        return len(self.floors_visited)
    
    def get_all_floors(self) -> List[int]:
        """Retourne tous les numéros d'étages, triés."""
        return sorted(self.floors.keys())
    
    def get_min_floor(self) -> int:
        """Retourne le numéro du plus bas étage."""
        return min(self.floors.keys()) if self.floors else MIN_FLOOR
    
    def get_max_floor(self) -> int:
        """Retourne le numéro du plus haut étage."""
        return max(self.floors.keys()) if self.floors else MAX_FLOOR
    
    def find_interactable(self, interactable_id: str) -> Tuple[Optional[int], Optional[Interactable]]:
        """
        Trouve un interactable dans tout le bâtiment.
        
        Args:
            interactable_id: ID de l'interactable
            
        Returns:
            Tuple (numéro_étage, interactable) ou (None, None)
        """
        for floor_num, floor in self.floors.items():
            interactable = floor.get_interactable(interactable_id)
            if interactable:
                return (floor_num, interactable)
        return (None, None)
    
    def find_npc(self, npc_id: str) -> Tuple[Optional[int], Optional[NPC]]:
        """
        Trouve un NPC dans tout le bâtiment.
        
        Args:
            npc_id: ID du NPC
            
        Returns:
            Tuple (numéro_étage, npc) ou (None, None)
        """
        for floor_num, floor in self.floors.items():
            npc = floor.get_npc(npc_id)
            if npc:
                return (floor_num, npc)
        return (None, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur le bâtiment.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        total_interactables = sum(len(floor.interactables) for floor in self.floors.values())
        total_npcs = sum(len(floor.npcs) for floor in self.floors.values())
        
        return {
            "total_floors": len(self.floors),
            "visited_floors": len(self.floors_visited),
            "total_interactables": total_interactables,
            "total_npcs": total_npcs,
            "elevator_x": self.elevator_x,
            "floor_height": self.floor_height
        }
