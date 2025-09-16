"""
Scène de gameplay principale pour A Day at the Office.
Gère le jeu complet avec building, ascenseur, tâches, etc.
"""

import logging
import pygame
from src.core.scene_manager import Scene
from src.core.input import InputAction
from src.settings import WIDTH, HEIGHT, DATA_PATH
from src.world.world_loader import WorldLoader
from src.ui.overlay import HUD, NotificationManager
from src.ui.dialogue import DialogueSystem
from src.core.utils import load_json_safe

logger = logging.getLogger(__name__)


class GameplayScene(Scene):
    """
    Scène de gameplay principale.
    
    Coordonne tous les systèmes : world, entities, UI, tasks, etc.
    """
    
    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        
        # Systèmes principaux
        self.world_loader = WorldLoader()
        self.hud = HUD()
        self.notification_manager = NotificationManager()
        self.dialogue_system = DialogueSystem()
        
        # État du jeu
        self.game_clock = None
        self.building = None
        self.elevator = None
        self.entity_manager = None
        self.task_manager = None
        
        # État de l'interface
        self.paused = False
        
        # Vue 3 étages fixe - plus besoin de caméra complexe
        
        # Données de localisation
        self.strings = {}
        
        logger.info("GameplayScene initialized")
    
    def enter(self, **kwargs):
        """Appelé en entrant dans la scène."""
        super().enter(**kwargs)
        
        # Créer l'horloge de jeu pour cette session
        from src.core.timer import GameClock
        from src.settings import START_TIME, END_TIME, GAME_SECONDS_PER_REAL_SECOND
        self.game_clock = GameClock(START_TIME, END_TIME, GAME_SECONDS_PER_REAL_SECOND)
        
        # Charger le monde
        if not self._load_world():
            logger.error("Failed to load world, returning to menu")
            self.switch_to("menu")
            return
        
        # Charger les chaînes de localisation
        self._load_strings()
        
        # Initialiser l'UI
        self._setup_ui()
        
        # Démarrer l'horloge de jeu
        if self.game_clock:
            self.game_clock.start()
        
        # Charger l'étage initial
        if self.building and self.entity_manager:
            player = self.entity_manager.get_player()
            if player:
                initial_floor = player.current_floor
                self.world_loader.change_player_floor(initial_floor)
        
        logger.info("Gameplay started")
    
    def _load_world(self) -> bool:
        """
        Charge tous les systèmes du monde.
        
        Returns:
            True si le chargement a réussi
        """
        success = self.world_loader.load_world()
        
        if success:
            # Récupérer les références aux systèmes
            self.building = self.world_loader.get_building()
            self.elevator = self.world_loader.get_elevator()
            self.entity_manager = self.world_loader.get_entity_manager()
            self.task_manager = self.world_loader.get_task_manager()
            
            logger.info("World systems loaded successfully")
        else:
            logger.error("Failed to load world systems")
            errors = self.world_loader.get_load_errors()
            for error in errors:
                logger.error(f"  - {error}")
        
        return success
    
    def _load_strings(self):
        """Charge les chaînes de localisation."""
        try:
            strings_path = DATA_PATH / "strings_fr.json"
            self.strings = load_json_safe(strings_path) or {}
            logger.debug("Localization strings loaded")
        except Exception as e:
            logger.error(f"Error loading strings: {e}")
            self.strings = {}
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        # Charger les polices
        self.hud.load_fonts()
        self.notification_manager.load_fonts()
        self.dialogue_system.load_fonts()
        
        # Charger les données de dialogue
        dialogue_path = DATA_PATH / "strings_fr.json"
        self.dialogue_system.load_dialogue_data(dialogue_path)
    
    def handle_event(self, event):
        """Gère les événements."""
        # Le dialogue a priorité sur tout
        if self.dialogue_system.is_active():
            consumed = self.dialogue_system.handle_event(event)
            if consumed:
                return
        
        # Gestion des événements HUD (icône tâches, panneau)
        if self.hud.handle_event(event):
            return
        
        # Gestion des événements globaux
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._handle_pause()
                return
            elif event.key == pygame.K_F5:
                # Recharger les assets avec nouvelles tailles
                from src.core.assets import asset_manager
                asset_manager.clear_cache()
                self.notification_manager.add_notification("Assets rechargés !", 2.0)
                return
            elif event.key == pygame.K_e:
                # Interaction
                if self.entity_manager:
                    player = self.entity_manager.get_player()
                    if player:
                        self._handle_interact(player)
                return
            elif event.key == pygame.K_c:
                # Appel ascenseur
                if self.entity_manager:
                    player = self.entity_manager.get_player()
                    if player:
                        self._handle_elevator_call(player)
                return
            elif pygame.K_0 <= event.key <= pygame.K_9:
                # Sélection d'étage
                floor_number = 90 + (event.key - pygame.K_0)
                self._handle_floor_selection(floor_number)
                return
        
        # Pour l'instant, gérer les entrées directement
        # TODO: Intégrer avec l'InputManager quand disponible
        pass
    
    def _handle_pause(self):
        """Gère la pause du jeu."""
        # Pour l'instant, retourner au menu au lieu de pause
        logger.info("Returning to menu (pause not fully implemented)")
        self.switch_to("menu")
    
    def update(self, dt):
        """Met à jour tous les systèmes."""
        if self.paused:
            return
        
        # Mettre à jour les systèmes world
        self._update_world_systems(dt)
        
        # Mettre à jour l'UI
        self._update_ui_systems(dt)
        
        # Gérer les interactions
        self._handle_interactions()
        
        # Vérifier les conditions de fin
        self._check_game_end_conditions()
    
    def _update_camera_for_floor(self, floor_number: int) -> None:
        """
        Met à jour la vue pour un étage donné (vue 3 étages).
        
        Args:
            floor_number: Numéro d'étage cible
        """
        # Plus besoin de caméra complexe avec la vue 3 étages fixe
        logger.debug(f"View updated for floor {floor_number}")
    
    def _update_world_systems(self, dt):
        """Met à jour les systèmes du monde."""
        # Récupérer les entrées directement de pygame pour l'instant
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        input_vector = (dx, dy)
        
        # Mettre à jour les entités
        if self.entity_manager:
            self.entity_manager.update(dt, input_vector)
        
        # Mettre à jour l'ascenseur et ajuster la caméra si nécessaire
        if self.elevator:
            old_floor = self.elevator.current_floor
            self.elevator.update(dt)
            
            # Si l'ascenseur a changé d'étage, déplacer le joueur s'il est dedans
            if old_floor != self.elevator.current_floor:
                # Si le joueur est dans l'ascenseur, le déplacer aussi
                if self.entity_manager:
                    player = self.entity_manager.get_player()
                    # Vérifier si le joueur est près de l'ascenseur
                    elevator_center_x = 30 + 40
                    if player and abs(player.x - elevator_center_x) < 60:
                        player.current_floor = self.elevator.current_floor
                        logger.info(f"Player moved to floor {self.elevator.current_floor}")
        
        # Plus besoin de mise à jour caméra avec vue 3 étages fixe
    
    def _update_ui_systems(self, dt):
        """Met à jour les systèmes d'interface."""
        self.notification_manager.update(dt)
        self.dialogue_system.update(dt)
    
    def _handle_interactions(self):
        """Gère les interactions du joueur."""
        if not self.entity_manager:
            return
        
        player = self.entity_manager.get_player()
        if not player:
            return
        
        # Les interactions seront gérées via les événements dans handle_event()
        # pour éviter les appels répétés à chaque frame
        pass
    
    def _handle_interact(self, player):
        """
        Gère l'interaction générale du joueur.
        
        Args:
            player: Le joueur
        """
        player_pos = player.get_position()
        current_floor = player.current_floor
        
        # Chercher des objets du nouveau système sur l'étage actuel
        if self.building:
            floor = self.building.get_floor(current_floor)
            if floor:
                nearby_object = self._find_nearby_floor_object(player_pos, floor.objects)
                if nearby_object:
                    self._interact_with_floor_object(nearby_object)
                    return
        
        # Fallback vers le système legacy
        # Chercher des NPCs proches
        nearby_npcs = self.entity_manager.get_nearby_npcs(player_pos)
        if nearby_npcs:
            npc = nearby_npcs[0]  # Prendre le premier
            self._interact_with_npc(npc)
            return
        
        # Chercher des objets interactifs legacy
        nearby_objects = self.entity_manager.get_nearby_interactables(player_pos)
        if nearby_objects:
            obj = nearby_objects[0]  # Prendre le premier
            self._interact_with_object(obj)
            return
        
        # Aucune interaction disponible
        self.notification_manager.add_notification("Rien à faire ici.", 2.0)
    
    def _find_nearby_floor_object(self, player_pos, objects_list):
        """
        Trouve un objet proche du joueur dans la liste d'objets de l'étage.
        
        Args:
            player_pos: Position du joueur (x, y)
            objects_list: Liste des objets de l'étage
            
        Returns:
            Objet proche ou None
        """
        world_x = 120  # Offset de la zone de jeu
        player_x = player_pos[0]
        
        for obj_data in objects_list:
            obj_x = world_x + obj_data.get('x', 0)
            
            # Calculer la distance horizontale (plus simple et plus fiable)
            distance = abs(player_x - obj_x)
            
            # Zone d'interaction élargie
            if distance < 100:  # Distance d'interaction plus généreuse
                return obj_data
        
        return None
    
    def _interact_with_floor_object(self, obj_data):
        """
        Interagit avec un objet du nouveau système.
        
        Args:
            obj_data: Données de l'objet depuis floors.json
        """
        kind = obj_data.get('kind', 'unknown')
        obj_id = obj_data.get('id', 'unknown')
        props = obj_data.get('props', {})
        
        if kind == "npc":
            # Interaction avec NPC
            name = props.get('name', 'Inconnu')
            dialogue_key = props.get('dialogue_key', '')
            
            if dialogue_key:
                # Démarrer le dialogue
                dialogue_started = self.dialogue_system.start_dialogue(dialogue_key, name)
                if dialogue_started:
                    self.notification_manager.add_notification(f"Conversation avec {name}", 2.0)
                else:
                    self.notification_manager.add_notification(f"Bonjour {name} !", 2.0)
            else:
                self.notification_manager.add_notification(f"Vous parlez à {name}", 2.0)
                
        elif kind in ["plant", "papers", "printer", "reception"]:
            # Interaction avec objet
            task_id = props.get('task_id', '')
            
            if task_id and self.task_manager:
                # Vérifier si la tâche est disponible
                task = self.task_manager.get_task(task_id)
                if task and self.task_manager.is_task_available(task_id):
                    success = self.task_manager.complete_task(task_id)
                    if success:
                        self.notification_manager.add_notification(f"Tâche terminée : {task.title}", 3.0)
                        
                        # Messages spécifiques selon le type
                        if kind == "plant":
                            self.notification_manager.add_notification("Plante arrosée !", 2.0)
                        elif kind == "papers":
                            self.notification_manager.add_notification("Papiers rangés !", 2.0)
                        elif kind == "printer":
                            self.notification_manager.add_notification("Imprimante réparée !", 2.0)
                        elif kind == "reception":
                            self.notification_manager.add_notification("Badge récupéré !", 2.0)
                    else:
                        self.notification_manager.add_notification("Tâche déjà terminée.", 2.0)
                else:
                    self.notification_manager.add_notification("Cette tâche n'est pas encore disponible.", 2.0)
            else:
                # Interaction simple sans tâche
                messages = {
                    "plant": "Vous regardez la plante.",
                    "papers": "Des papiers éparpillés.",
                    "printer": "L'imprimante ronronne.",
                    "reception": "Le bureau d'accueil."
                }
                message = messages.get(kind, f"Vous examinez {kind}.")
                self.notification_manager.add_notification(message, 2.0)
        else:
            # Objet inconnu
            self.notification_manager.add_notification(f"Vous examinez {obj_id}.", 2.0)
    
    def _interact_with_npc(self, npc):
        """
        Interagit avec un NPC.
        
        Args:
            npc: Le NPC avec qui interagir
        """
        # Démarrer le dialogue
        dialogue_started = self.dialogue_system.start_dialogue(npc.dialogue_id, npc.name)
        
        if dialogue_started:
            # Marquer la conversation
            dialogue_result = npc.talk()
            
            # Vérifier si c'est lié à une tâche
            if self.task_manager:
                task = self.task_manager.get_task_for_npc(npc.id)
                if task and self.task_manager.is_task_available(task.id):
                    self.task_manager.complete_task(task.id)
                    self.notification_manager.add_notification(f"Tâche terminée : {task.title}", 3.0)
        else:
            self.notification_manager.add_notification(f"Conversation avec {npc.name}", 2.0)
    
    def _interact_with_object(self, obj):
        """
        Interagit avec un objet.
        
        Args:
            obj: L'objet avec lequel interagir
        """
        if obj.interact():
            # Vérifier si c'est lié à une tâche
            if self.task_manager and obj.task_id:
                task = self.task_manager.get_task(obj.task_id)
                if task and self.task_manager.is_task_available(task.id):
                    success = self.task_manager.complete_task(task.id)
                    if success:
                        self.notification_manager.add_notification(task.completion_message, 3.0)
                        self.notification_manager.add_notification(f"Tâche terminée : {task.title}", 3.0)
            else:
                self.notification_manager.add_notification("Action effectuée.", 2.0)
        else:
            self.notification_manager.add_notification("Impossible d'interagir.", 2.0)
    
    def _handle_elevator_call(self, player):
        """
        Gère l'appel de l'ascenseur.
        
        Args:
            player: Le joueur
        """
        if not self.elevator or not self.building:
            return
        
        # Position de l'ascenseur (fixe à gauche)
        elevator_x = 30 + 40  # Centre de l'ascenseur
        
        # Vérifier si le joueur est proche de l'ascenseur (zone plus large)
        distance = abs(player.x - elevator_x)
        if distance < 60:  # Zone d'interaction plus large
            if self.elevator.current_floor == player.current_floor:
                # L'ascenseur est déjà à cet étage
                self.notification_manager.add_notification("Entrez dans l'ascenseur et choisissez un étage (0-9).", 3.0)
            else:
                # Appeler l'ascenseur
                self.elevator.call(player.current_floor)
                self.notification_manager.add_notification(f"Ascenseur appelé à l'étage {player.current_floor}.", 2.0)
        else:
            self.notification_manager.add_notification("Approchez-vous de l'ascenseur.", 2.0)
    
    def _handle_floor_selection(self, floor_number):
        """
        Gère la sélection d'étage.
        
        Args:
            floor_number: Numéro d'étage sélectionné
        """
        if not self.elevator or not self.building:
            return
        
        if self.building.has_floor(floor_number):
            player = self.entity_manager.get_player()
            if player:
                # Position de l'ascenseur (fixe à gauche)
                elevator_x = 30 + 40  # Centre de l'ascenseur
                distance = abs(player.x - elevator_x)
                
                if distance < 60:  # Zone d'interaction
                    if self.elevator.current_floor == player.current_floor:
                        # Le joueur peut utiliser l'ascenseur
                        self.elevator.go_to(floor_number)
                        self.notification_manager.add_notification(f"Direction étage {floor_number}", 2.0)
                        
                        # Le joueur change d'étage immédiatement (simulation rapide)
                        player.current_floor = floor_number
                        logger.info(f"Player instantly moved to floor {floor_number}")
                    else:
                        self.notification_manager.add_notification("Appelez d'abord l'ascenseur (C).", 2.0)
                else:
                    self.notification_manager.add_notification("Approchez-vous de l'ascenseur.", 2.0)
        else:
            self.notification_manager.add_notification(f"Étage {floor_number} inexistant.", 2.0)
    
    def _change_player_floor(self, new_floor):
        """
        Change l'étage du joueur.
        
        Args:
            new_floor: Nouvel étage
        """
        success = self.world_loader.change_player_floor(new_floor)
        if success:
            self.notification_manager.add_notification(f"Arrivé à l'étage {new_floor}", 2.0)
        else:
            self.notification_manager.add_notification("Erreur lors du changement d'étage.", 2.0)
    
    def _check_game_end_conditions(self):
        """Vérifie les conditions de fin de jeu."""
        # TODO: Fix 'bool' object is not callable error
        # if self.game_clock and self.game_clock.is_deadline():
        #     # Temps écoulé - aller au résumé
        #     logger.info("Game deadline reached, going to summary")
        #     self.switch_to("summary")
        pass
    
    def draw(self, screen):
        """Dessine la scène."""
        # Fond dégradé plus agréable
        for y in range(HEIGHT):
            # Dégradé du gris clair vers gris foncé
            color_value = int(220 - (y / HEIGHT) * 80)  # 220 -> 140
            color = (color_value, color_value, color_value)
            pygame.draw.line(screen, color, (0, y), (WIDTH, y))
        
        # Dessiner le monde (simplifié pour l'instant)
        self._draw_world(screen)
        
        # Dessiner l'UI
        self._draw_ui(screen)
        
        # Debug supprimé - logs console uniquement
    
    def _draw_world(self, screen):
        """Dessine les éléments du monde avec caméra, fonds d'étage et ordre correct."""
        from src.core.assets import asset_manager
        
        if not self.entity_manager or not self.building:
            return
            
        player = self.entity_manager.get_player()
        if not player:
            return
        
        # Configuration vue multi-étages (3 étages visibles)
        floor_height = HEIGHT // 3  # Chaque étage prend 1/3 de l'écran
        world_width = WIDTH - 150  # Largeur de la zone de jeu
        world_x = 120  # Position X de début de la zone de jeu
        
        # Vue 3 étages fixe - pas besoin d'offset caméra
        
        # Déterminer les 3 étages visibles
        current_floor = player.current_floor
        
        # Si on est au dernier étage, on le place en bas
        # Si on est au premier étage, on le place en haut
        # Sinon on le centre
        all_floors = sorted(self.building.floors.keys())
        current_index = all_floors.index(current_floor) if current_floor in all_floors else 0
        
        # Déterminer les 3 étages à afficher
        if current_index >= len(all_floors) - 1:
            # Dernier étage : afficher les 3 derniers (étage actuel en bas)
            visible_floors = all_floors[-3:] if len(all_floors) >= 3 else all_floors
        elif current_index == 0:
            # Premier étage : afficher les 3 premiers (étage actuel en haut)
            visible_floors = all_floors[:3] if len(all_floors) >= 3 else all_floors
        else:
            # Étage intermédiaire : centrer
            start_idx = max(0, current_index - 1)
            end_idx = min(len(all_floors), start_idx + 3)
            visible_floors = all_floors[start_idx:end_idx]
        
        # Trier les étages par ordre croissant pour un rendu correct
        visible_floors.sort()
        
        # Dessiner chaque étage visible (du plus haut au plus bas à l'écran)
        for i, floor_num in enumerate(reversed(visible_floors)):  # Inverser pour avoir le plus haut en haut
            floor = self.building.get_floor(floor_num)
            if not floor:
                continue
            
            # Position Y à l'écran : étage du haut = Y=0, étage du bas = Y=400
            screen_y = i * floor_height
            
            # 1. Dessiner le fond d'étage
            floor_rect = pygame.Rect(world_x, screen_y, world_width, floor_height - 10)
            
            if floor.background_surface:
                # Utiliser le fond personnalisé
                bg_scaled = pygame.transform.scale(floor.background_surface, (world_width, floor_height - 10))
                screen.blit(bg_scaled, (world_x, screen_y))
            else:
                # Fond par défaut
                color = (240, 240, 240) if floor_num == current_floor else (200, 200, 200)
                pygame.draw.rect(screen, color, floor_rect)
            
            # Bordure de l'étage
            pygame.draw.rect(screen, (100, 100, 100), floor_rect, 2)
            
            # Numéro d'étage (seulement si c'est l'étage actuel)
            if floor_num == current_floor:
                font = pygame.font.SysFont(None, 28)
                floor_text = f"Étage {floor_num} - {floor.name}"
                text_surface = font.render(floor_text, True, (255, 255, 255))
                # Fond semi-transparent pour le texte
                text_bg = pygame.Surface((text_surface.get_width() + 10, text_surface.get_height() + 4))
                text_bg.fill((0, 0, 0))
                text_bg.set_alpha(150)
                screen.blit(text_bg, (5, screen_y + 5))
                screen.blit(text_surface, (10, screen_y + 7))
            
            # 2. Dessiner l'ascenseur (même taille que l'étage)
            if self.elevator:
                elevator_sprite = asset_manager.get_image("elevator")
                
                # L'ascenseur doit être bien visible et proportionnel
                elevator_width = 60  # Largeur raisonnable
                elevator_height = floor_height - 30  # Hauteur qui tient dans l'étage
                
                # Redimensionner en gardant les proportions si nécessaire
                if elevator_sprite.get_height() > 0:
                    ratio = min(elevator_width / elevator_sprite.get_width(), 
                              elevator_height / elevator_sprite.get_height())
                    final_width = int(elevator_sprite.get_width() * ratio)
                    final_height = int(elevator_sprite.get_height() * ratio)
                else:
                    final_width, final_height = elevator_width, elevator_height
                
                elevator_resized = pygame.transform.scale(elevator_sprite, (final_width, final_height))
                
                # Positionner l'ascenseur à gauche
                elevator_x = 30  # Position fixe à gauche
                elevator_y = screen_y + (floor_height - final_height) // 2
                screen.blit(elevator_resized, (elevator_x, elevator_y))
                
                # Indicateur si l'ascenseur est à cet étage
                if self.elevator.current_floor == floor_num:
                    # Porte ouverte/fermée
                    if hasattr(self.elevator, 'doors_open') and self.elevator.doors_open:
                        pygame.draw.rect(screen, (0, 255, 0), 
                                       (elevator_x - 5, elevator_y, 5, final_height))
                    else:
                        pygame.draw.rect(screen, (255, 255, 0), 
                                       (elevator_x - 5, elevator_y, 5, final_height))
            
            # 3. Dessiner les objets de l'étage (nouveau système)
            for obj_data in floor.objects:
                self._draw_floor_object(screen, obj_data, world_x, screen_y, floor_height)
            
            # 4. Dessiner le joueur s'il est sur cet étage
            if floor_num == current_floor and self.entity_manager:
                player = self.entity_manager.get_player()
                if player:
                    player_sprite = asset_manager.get_image("player_idle")
                    player_x = player.x - player_sprite.get_width() // 2
                    # Positionner le joueur au sol (bas de l'étage)
                    player_y = screen_y + floor_height - player_sprite.get_height() - 5
                    screen.blit(player_sprite, (player_x, player_y))
            
            # 5. Dessiner les entités legacy (compatibilité) - sur tous les étages
            if self.entity_manager:
                # NPCs legacy
                for npc in self.entity_manager.npcs.values():
                    if getattr(npc, 'current_floor', current_floor) == floor_num:
                        npc_sprite = asset_manager.get_image("npc_generic")
                        npc_x = npc.x - npc_sprite.get_width() // 2
                        npc_y = screen_y + floor_height - npc_sprite.get_height() - 15
                        screen.blit(npc_sprite, (npc_x, npc_y))
                
                # Objets interactifs legacy
                for obj in self.entity_manager.interactables.values():
                    if getattr(obj, 'current_floor', current_floor) == floor_num:
                        self._draw_legacy_object(screen, obj, screen_y, floor_height)
    
    def _draw_floor_object(self, screen, obj_data: dict, world_x: int, screen_y: int, floor_height: int) -> None:
        """
        Dessine un objet positionné sur un étage.
        
        Args:
            screen: Surface de rendu
            obj_data: Données de l'objet depuis floors.json
            world_x: Position X de début de la zone de jeu
            screen_y: Position Y de l'étage à l'écran
            floor_height: Hauteur d'un étage
        """
        from src.core.assets import asset_manager
        
        kind = obj_data.get("kind", "unknown")
        obj_x = obj_data.get("x", 0)
        obj_y = obj_data.get("y", 0)
        props = obj_data.get("props", {})
        
        # Calculer la position à l'écran (objets posés au sol)
        screen_obj_x = world_x + obj_x
        
        # Choisir le sprite selon le kind
        sprite_key = self._get_sprite_key_for_kind(kind)
        if sprite_key:
            obj_sprite = asset_manager.get_image(sprite_key)
            
            # Positionner l'objet au sol de l'étage
            final_x = screen_obj_x - obj_sprite.get_width() // 2
            
            # Les objets sont posés au sol (bas de l'étage)
            if kind == "npc":
                # NPCs debout sur le sol
                final_y = screen_y + floor_height - obj_sprite.get_height() - 5
            else:
                # Objets posés sur le sol
                final_y = screen_y + floor_height - obj_sprite.get_height() - 5
            
            # Effets spéciaux selon les props
            if kind in ["plant"] and props.get("thirst", 0) > 0.7:
                # Plante assoiffée - teinter en jaune
                tinted_sprite = obj_sprite.copy()
                tinted_sprite.fill((255, 255, 0, 50), special_flags=pygame.BLEND_ADD)
                screen.blit(tinted_sprite, (final_x, final_y))
            elif kind == "printer" and props.get("jammed", False):
                # Imprimante bloquée - teinter en rouge
                tinted_sprite = obj_sprite.copy()
                tinted_sprite.fill((255, 0, 0, 50), special_flags=pygame.BLEND_ADD)
                screen.blit(tinted_sprite, (final_x, final_y))
            else:
                screen.blit(obj_sprite, (final_x, final_y))
            
            # Debug visuel : zone d'interaction (temporaire)
            if kind != "decoration":  # Seulement pour les objets interactifs
                pygame.draw.circle(screen, (255, 0, 0, 50), (int(screen_obj_x), int(final_y + obj_sprite.get_height()//2)), 100, 2)
    
    def _get_sprite_key_for_kind(self, kind: str) -> str:
        """
        Retourne la clé de sprite pour un type d'objet donné.
        
        Args:
            kind: Type d'objet (plant, papers, npc, etc.)
            
        Returns:
            Clé de sprite dans le manifest
        """
        sprite_mapping = {
            "plant": "interactable_plant",
            "papers": "interactable_papers", 
            "printer": "interactable_printer",
            "npc": "npc_generic",
            "decoration": "interactable_plant",  # Fallback
            "lightbulb": "interactable_papers",  # Fallback
            "filing_cabinet": "interactable_printer",  # Fallback
            "server": "interactable_printer",  # Fallback
            "presentation": "interactable_papers",  # Fallback
            "phone": "interactable_papers",  # Fallback
            "boxes": "interactable_papers",  # Fallback
            "reception": "interactable_printer",  # Fallback
        }
        return sprite_mapping.get(kind, "interactable_plant")
    
    def _draw_legacy_object(self, screen, obj, screen_y: int, floor_height: int) -> None:
        """
        Dessine un objet du système legacy pour compatibilité.
        
        Args:
            screen: Surface de rendu
            obj: Objet legacy
            screen_y: Position Y de l'étage à l'écran
            floor_height: Hauteur d'un étage
        """
        from src.core.assets import asset_manager
        
        # Choisir le bon sprite selon le type d'objet
        if obj.type == "plant":
            obj_sprite = asset_manager.get_image("interactable_plant")
        elif obj.type == "papers":
            obj_sprite = asset_manager.get_image("interactable_papers")
        elif obj.type == "printer":
            obj_sprite = asset_manager.get_image("interactable_printer")
        else:
            obj_sprite = asset_manager.get_image("interactable_plant")
        
        # Griser si déjà interagi
        if obj.interacted:
            gray_sprite = obj_sprite.copy()
            gray_sprite.fill((128, 128, 128, 128), special_flags=pygame.BLEND_MULT)
            obj_sprite = gray_sprite
        
        obj_x = obj.x - obj_sprite.get_width() // 2
        obj_y = screen_y + floor_height - obj_sprite.get_height() - 10
        screen.blit(obj_sprite, (obj_x, obj_y))
    
    def _draw_ui(self, screen):
        """Dessine l'interface utilisateur."""
        # HUD principal
        if self.game_clock and self.task_manager:
            current_time = self.game_clock.get_time_str()
            progress = self.game_clock.get_progress()
            
            self.hud.draw_clock(screen, current_time, progress)
            
            # Tâches
            available_tasks = self.task_manager.get_available_tasks()
            task_statuses = {task.id: self.task_manager.get_task_status(task.id) 
                           for task in self.task_manager.tasks.values()}
            self.hud.draw_tasks(screen, available_tasks, task_statuses)
            
            # Indicateur d'étage
            if self.entity_manager:
                player = self.entity_manager.get_player()
                if player and self.building:
                    floor = self.building.get_floor(player.current_floor)
                    floor_name = floor.name if floor else ""
                    self.hud.draw_floor_indicator(screen, player.current_floor, floor_name)
        
        # Indication d'interaction
        self._update_interaction_hint()
        self.hud.draw_interaction_hint(screen)
        
        # Notifications
        self.notification_manager.draw(screen)
        
        # Dialogue
        self.dialogue_system.draw(screen)
    
    def _update_interaction_hint(self):
        """Met à jour l'indication d'interaction."""
        if not self.entity_manager:
            self.hud.hide_interaction_hint()
            return
        
        player = self.entity_manager.get_player()
        if not player:
            self.hud.hide_interaction_hint()
            return
        
        player_pos = player.get_position()
        current_floor = player.current_floor
        
        # Vérifier les objets du nouveau système en priorité
        if self.building:
            floor = self.building.get_floor(current_floor)
            if floor:
                nearby_object = self._find_nearby_floor_object(player_pos, floor.objects)
                if nearby_object:
                    kind = nearby_object.get('kind', 'objet')
                    props = nearby_object.get('props', {})
                    
                    if kind == "npc":
                        name = props.get('name', 'Personne')
                        self.hud.show_interaction_hint(f"E : Parler à {name}")
                        return
                    else:
                        action_names = {
                            "plant": "Arroser",
                            "papers": "Ranger", 
                            "printer": "Utiliser",
                            "reception": "Utiliser"
                        }
                        action = action_names.get(kind, "Examiner")
                        self.hud.show_interaction_hint(f"E : {action} {kind}")
                        return
        
        # Fallback vers le système legacy
        nearby_npcs = self.entity_manager.get_nearby_npcs(player_pos)
        nearby_objects = self.entity_manager.get_nearby_interactables(player_pos)
        
        if nearby_npcs:
            npc = nearby_npcs[0]
            self.hud.show_interaction_hint(f"E : Parler à {npc.name}")
        elif nearby_objects:
            obj = nearby_objects[0]
            self.hud.show_interaction_hint(f"E : Utiliser {obj.type}")
        else:
            # Vérifier si proche de l'ascenseur
            if self.elevator:
                elevator_x = 30 + 40  # Centre de l'ascenseur
                distance = abs(player.x - elevator_x)
                if distance < 60:
                    if self.elevator.current_floor == player.current_floor:
                        self.hud.show_interaction_hint("0-9 : Choisir étage")
                    else:
                        self.hud.show_interaction_hint("C : Appeler ascenseur")
                else:
                    self.hud.hide_interaction_hint()
    
    
    def exit(self):
        """Appelé en quittant la scène."""
        super().exit()
        
        # Arrêter l'horloge
        if self.game_clock:
            self.game_clock.stop()
        
        logger.info("Exited GameplayScene")
