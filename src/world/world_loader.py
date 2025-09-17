"""
Chargeur du monde de jeu pour A Day at the Office.
Initialise le bâtiment, les tâches, et coordonne tous les systèmes world.
"""

import logging
import random
from typing import Optional, Dict, Any, List
from pathlib import Path

from src.settings import DATA_PATH
from src.world.building import Building
from src.world.elevator import Elevator
from src.world.entities import EntityManager
from src.world.tasks import TaskManager
from src.core.utils import load_json_safe
from src.core.assets import asset_manager

logger = logging.getLogger(__name__)


class WorldLoader:
    """
    Charge et initialise tous les systèmes du monde de jeu.
    """
    
    def __init__(self):
        # Systèmes principaux
        self.building: Optional[Building] = None
        self.elevator: Optional[Elevator] = None
        self.entity_manager: Optional[EntityManager] = None
        self.task_manager: Optional[TaskManager] = None
        
        # État du chargement
        self.is_loaded = False
        self.load_errors: list[str] = []
        
        # Sprites d'employés disponibles pour la randomisation
        self.available_employee_sprites = [
            "employee_1", "employee_2", "employee_3", "employee_4", "employee_5",
            "employee_6", "employee_7", "employee_8", "employee_9"
        ]
        
        logger.info("WorldLoader initialized")
    
    def load_world(self) -> bool:
        """
        Charge complètement le monde de jeu.
        
        Returns:
            True si le chargement a réussi
        """
        self.load_errors.clear()
        
        try:
            # 1. Initialiser les systèmes
            self.building = Building()
            self.elevator = Elevator()
            self.entity_manager = EntityManager()
            self.task_manager = TaskManager()
            
            # 2. Charger les données des étages
            if not self._load_building_data():
                self.load_errors.append("Failed to load building data")
            
            # 2.1. Randomiser les sprites d'employés
            self._randomize_employee_sprites()
            
            # 2.5. Charger les fonds d'étage
            self._load_floor_backgrounds()
            
            # 3. Charger les tâches
            if not self._load_tasks_data():
                self.load_errors.append("Failed to load tasks data")
            
            # 4. Configurer l'ascenseur
            self._configure_elevator()
            
            # 5. Créer le joueur
            self._create_player()
            
            # Vérifier si le chargement est réussi
            self.is_loaded = len(self.load_errors) == 0
            
            if self.is_loaded:
                logger.info("World loaded successfully")
            else:
                logger.error(f"World loading failed with {len(self.load_errors)} errors")
                for error in self.load_errors:
                    logger.error(f"  - {error}")
            
            return self.is_loaded
            
        except Exception as e:
            logger.error(f"Critical error loading world: {e}")
            self.load_errors.append(f"Critical error: {e}")
            return False
    
    def _load_building_data(self) -> bool:
        """
        Charge les données du bâtiment depuis floors.json.
        
        Returns:
            True si le chargement a réussi
        """
        try:
            floors_path = DATA_PATH / "floors.json"
            floors_data = load_json_safe(floors_path)
            
            if not floors_data:
                logger.error(f"Could not load floors data from {floors_path}")
                return False
            
            return self.building.load_from_data(floors_data)
            
        except Exception as e:
            logger.error(f"Error loading building data: {e}")
            return False
    
    def _randomize_employee_sprites(self) -> None:
        """
        Randomise les sprites des employés pour chaque partie.
        Assigne aléatoirement des sprites employee_* aux NPCs.
        """
        if not self.building:
            return
        
        try:
            # Collecter tous les NPCs qui n'ont pas de sprite_key spécifique
            npcs_to_randomize = []
            for floor in self.building.floors.values():
                # Vérifier les NPCs dans le nouveau système objects
                for obj in floor.objects:
                    if obj.get("kind") == "npc":
                        props = obj.get("props", {})
                        sprite_key = props.get("sprite_key", "npc_generic")
                        # Si le NPC n'a pas de sprite_key spécifique, le marquer pour randomisation
                        if sprite_key == "npc_generic":
                            npcs_to_randomize.append(obj)
                
                # Vérifier aussi les NPCs legacy
                for npc in floor.npcs:
                    # Si le NPC n'a pas de sprite_key ou utilise npc_generic, le randomiser
                    if not hasattr(npc, 'sprite_key') or npc.sprite_key == "npc_generic":
                        npcs_to_randomize.append(npc)
            
            # Mélanger la liste des sprites disponibles
            available_sprites = self.available_employee_sprites.copy()
            random.shuffle(available_sprites)
            
            # Assigner aléatoirement les sprites
            for i, npc in enumerate(npcs_to_randomize):
                if i < len(available_sprites):
                    sprite = available_sprites[i]
                else:
                    # Si on a plus de sprites que de NPCs, réutiliser les sprites
                    sprite_index = i % len(available_sprites)
                    sprite = available_sprites[sprite_index]
                
                # Assigner le sprite selon le type de NPC
                if isinstance(npc, dict):
                    # Nouveau système objects
                    if "props" not in npc:
                        npc["props"] = {}
                    npc["props"]["sprite_key"] = sprite
                    npc_name = npc.get("props", {}).get("name", "Unknown")
                    logger.debug(f"Assigned sprite {sprite} to NPC {npc_name}")
                else:
                    # Système legacy
                    npc.sprite_key = sprite
                    logger.debug(f"Assigned sprite {sprite} to NPC {npc.name}")
            
            logger.info(f"Randomized sprites for {len(npcs_to_randomize)} NPCs")
            
        except Exception as e:
            logger.error(f"Error randomizing employee sprites: {e}")
    
    def _load_floor_backgrounds(self) -> None:
        """Charge les fonds d'étage via l'AssetManager."""
        if not self.building:
            return
        
        try:
            from src.core.assets import asset_manager
            
            # Obtenir la clé de fond par défaut depuis floors.json
            floors_path = DATA_PATH / "floors.json"
            floors_data = load_json_safe(floors_path)
            default_bg_key = floors_data.get("default_bg_key", "floor_default") if floors_data else "floor_default"
            
            # Charger le fond pour chaque étage
            for floor in self.building.floors.values():
                floor.load_background(asset_manager, default_bg_key)
            
            logger.info("Floor backgrounds loaded")
            
        except Exception as e:
            logger.error(f"Error loading floor backgrounds: {e}")
    
    def _load_tasks_data(self) -> bool:
        """
        Charge les données des tâches depuis tasks.json.
        
        Returns:
            True si le chargement a réussi
        """
        try:
            tasks_path = DATA_PATH / "tasks.json"
            return self.task_manager.load_from_json(tasks_path)
            
        except Exception as e:
            logger.error(f"Error loading tasks data: {e}")
            return False
    
    def _configure_elevator(self) -> None:
        """Configure l'ascenseur avec les données du bâtiment."""
        if self.building and self.elevator:
            # Utiliser la position X de l'ascenseur du bâtiment
            self.elevator.x = self.building.elevator_x
            
            # Définir l'étage de départ: bureau du boss (dernier étage)
            boss_floor = self.building.get_max_floor()
            self.elevator.current_floor = boss_floor
            self.elevator.display_floor = float(boss_floor)
            try:
                # Ouvrir les portes au démarrage
                from src.world.elevator import ElevatorState
                self.elevator.state = ElevatorState.DOORS_OPEN
            except Exception:
                pass
            
            logger.debug(f"Elevator configured at x={self.elevator.x}, floor={boss_floor}")
    
    def _create_player(self) -> None:
        """Crée le joueur à la position initiale."""
        if self.entity_manager and self.building:
            # Position initiale près de l'ascenseur au lobby
            start_x = self.building.elevator_x + 100  # Un peu à droite de l'ascenseur
            start_y = 0.0  # Position Y du monde (baseline gérée par le rendu)
            
            player = self.entity_manager.create_player(start_x, start_y)
            
            # Définir l'étage initial: bureau du boss (dernier étage)
            boss_floor = self.building.get_max_floor()
            player.set_floor(boss_floor)
            # Désactiver l'auto-scale pour éviter les problèmes de positionnement
            # Le joueur utilisera la taille définie dans assets_manifest.json
            # try:
            #     floor = self.building.get_floor(boss_floor)
            #     if floor is not None:
            #         player.apply_floor_geometry(getattr(floor, "geometry", {}), asset_manager)
            # except Exception:
            #     pass
            
            logger.info(f"Player created at ({start_x}, {start_y}) on floor {boss_floor}")
    
    def load_floor_entities(self, floor_number: int) -> bool:
        """
        Charge les entités (NPCs, objets) d'un étage spécifique.
        
        Args:
            floor_number: Numéro de l'étage à charger
            
        Returns:
            True si le chargement a réussi
        """
        if not self.is_loaded or not self.building or not self.entity_manager:
            logger.error("World not loaded, cannot load floor entities")
            return False
        
        floor = self.building.get_floor(floor_number)
        if not floor:
            logger.warning(f"Floor {floor_number} not found")
            return False
        
        try:
            # Vider les entités existantes
            self.entity_manager.clear_floor_entities()
            
            # Charger les NPCs
            for npc_data in floor.npcs:
                self.entity_manager.add_npc(
                    npc_data.id,
                    npc_data.name,
                    npc_data.x,
                    npc_data.y,
                    npc_data.dialogue_id
                )
            
            # Charger les objets interactifs
            for interactable_data in floor.interactables:
                self.entity_manager.add_interactable(
                    interactable_data.id,
                    interactable_data.type,
                    interactable_data.x,
                    interactable_data.y,
                    interactable_data.task_id
                )
            
            logger.debug(f"Loaded entities for floor {floor_number}: {len(floor.npcs)} NPCs, {len(floor.interactables)} objects")
            return True
            
        except Exception as e:
            logger.error(f"Error loading floor {floor_number} entities: {e}")
            return False
    
    def change_player_floor(self, new_floor: int) -> bool:
        """
        Change l'étage du joueur et charge les entités correspondantes.
        
        Args:
            new_floor: Nouveau numéro d'étage
            
        Returns:
            True si le changement a réussi
        """
        if not self.is_loaded:
            return False
        
        # Vérifier que l'étage existe
        if not self.building.has_floor(new_floor):
            logger.warning(f"Floor {new_floor} does not exist")
            return False
        
        # Mettre à jour le joueur
        if self.entity_manager and self.entity_manager.get_player():
            player = self.entity_manager.get_player()
            player.set_floor(new_floor)
            # Adapter la géométrie d'étage
            # Désactiver l'auto-scale pour éviter les problèmes de positionnement
            # try:
            #     floor = self.building.get_floor(new_floor)
            #     if floor is not None:
            #         player.apply_floor_geometry(getattr(floor, "geometry", {}), asset_manager)
            # except Exception:
            #     pass
            
            # Marquer l'étage comme visité
            self.building.visit_floor(new_floor)
        
        # Charger les entités de l'étage
        return self.load_floor_entities(new_floor)
    
    def get_building(self) -> Optional[Building]:
        """Retourne le bâtiment."""
        return self.building
    
    def get_elevator(self) -> Optional[Elevator]:
        """Retourne l'ascenseur."""
        return self.elevator
    
    def get_entity_manager(self) -> Optional[EntityManager]:
        """Retourne le gestionnaire d'entités."""
        return self.entity_manager
    
    def get_task_manager(self) -> Optional[TaskManager]:
        """Retourne le gestionnaire de tâches."""
        return self.task_manager
    
    def is_world_loaded(self) -> bool:
        """Vérifie si le monde est chargé."""
        return self.is_loaded
    
    def get_load_errors(self) -> list[str]:
        """Retourne les erreurs de chargement."""
        return self.load_errors.copy()
    
    def reload_world(self) -> bool:
        """
        Recharge complètement le monde.
        
        Returns:
            True si le rechargement a réussi
        """
        logger.info("Reloading world...")
        
        # Réinitialiser l'état
        self.is_loaded = False
        self.load_errors.clear()
        
        # Recharger
        return self.load_world()
    
    def get_world_stats(self) -> Dict[str, Any]:
        """
        Retourne des statistiques globales sur le monde.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        stats = {
            "is_loaded": self.is_loaded,
            "load_errors_count": len(self.load_errors),
            "systems_initialized": {
                "building": self.building is not None,
                "elevator": self.elevator is not None,
                "entity_manager": self.entity_manager is not None,
                "task_manager": self.task_manager is not None
            }
        }
        
        # Ajouter les stats des sous-systèmes si disponibles
        if self.building:
            stats["building"] = self.building.get_stats()
        
        if self.elevator:
            stats["elevator"] = self.elevator.get_stats()
        
        if self.entity_manager:
            stats["entities"] = self.entity_manager.get_stats()
        
        if self.task_manager:
            stats["tasks"] = self.task_manager.get_stats()
        
        return stats
    
    def validate_world_integrity(self) -> list[str]:
        """
        Valide l'intégrité du monde chargé.
        
        Returns:
            Liste des problèmes trouvés (vide si tout va bien)
        """
        issues = []
        
        if not self.is_loaded:
            issues.append("World is not loaded")
            return issues
        
        # Vérifier les références des tâches
        if self.task_manager and self.building:
            for task in self.task_manager.get_main_tasks() + self.task_manager.get_side_tasks():
                # Vérifier les étages
                if task.floor and not self.building.has_floor(task.floor):
                    issues.append(f"Task '{task.id}' references non-existent floor {task.floor}")
                
                # Vérifier les objets interactifs
                if task.interactable_id:
                    floor_num, interactable = self.building.find_interactable(task.interactable_id)
                    if not interactable:
                        issues.append(f"Task '{task.id}' references non-existent interactable '{task.interactable_id}'")
                
                # Vérifier les NPCs
                if task.npc_id:
                    floor_num, npc = self.building.find_npc(task.npc_id)
                    if not npc:
                        issues.append(f"Task '{task.id}' references non-existent NPC '{task.npc_id}'")
        
        # Vérifier les dépendances des tâches
        if self.task_manager:
            for task in self.task_manager.tasks.values():
                for dep_id in task.dependencies:
                    if dep_id not in self.task_manager.tasks:
                        issues.append(f"Task '{task.id}' has invalid dependency '{dep_id}'")
        
        if issues:
            logger.warning(f"World integrity check found {len(issues)} issues")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("World integrity check passed")
        
        return issues
