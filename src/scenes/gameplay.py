"""
Scène de gameplay principale pour A Day at the Office.
Gère le jeu complet avec building, ascenseur, tâches, etc.
"""

import logging
from typing import Optional
import pygame
from src.core.scene_manager import Scene
from src.core.input import InputAction
from src.settings import WIDTH, HEIGHT, DATA_PATH
from src.world.world_loader import WorldLoader
from src.ui.overlay import HUD, NotificationManager
from src.ui.dialogue import DialogueSystem
from src.ui.speech_bubbles import SpeechBubbleManager
from src.world.npc_movement import NPCMovementManager
from src.core.utils import load_json_safe
from src.core.event_bus import event_bus, TIME_TICK, TIME_REACHED
from src.settings import DATA_PATH

import os
import time
import random
from typing import Optional
logger = logging.getLogger(__name__)

try:
    import moviepy as mpy
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logger.warning("MoviePy not available, final video will be skipped")


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
        self.speech_bubbles = SpeechBubbleManager()
        self.npc_movement_manager = NPCMovementManager()

        # État du jeu
        self.game_clock = None
        self.building = None
        self.elevator = None
        self.entity_manager = None
        self.task_manager = None
        self.flags = set()
        self._intro_lock_active = True
        self._printer_requirement = 2
        self._subscriptions = []

        # État de l'interface
        self.paused = False
        
        # Vue 3 étages fixe - plus besoin de caméra complexe
        
        # Données de localisation
        self.strings = {}
        
        # Map des PNJ runtime (source unique de vérité)
        self.runtime_npcs = {}  # id -> objet PNJ runtime (celui que déplace NPCMovement)

        logger.info("GameplayScene initialized")
    
    def enter(self, **kwargs):
        """Appelé en entrant dans la scène."""
        super().enter(**kwargs)
        
        # Utiliser l'horloge globale fournie par l'app (source de vérité)
        self.game_clock = self.scene_manager.context.get("game_clock")
        
        # Charger le monde
        if not self._load_world():
            logger.error("Failed to load world, returning to menu")
            self.switch_to("menu")
            return
        
        # Charger les chaînes de localisation
        self._load_strings()
        
        # Initialiser l'UI
        self._setup_ui()
        
        # Démarrer l'horloge si nouvellement créée (sinon l'app la gère)
        if self.game_clock and not self.game_clock.is_running:
            try:
                self.game_clock.start()
            except Exception:
                pass

        # S'abonner aux événements temporels et timeline
        self._subscribe_events()
        
        # Charger l'étage initial
        if self.building and self.entity_manager:
            player = self.entity_manager.get_player()
            if player:
                initial_floor = player.current_floor
                self.world_loader.change_player_floor(initial_floor)

        # Initialiser le mouvement des NPCs
        self._setup_npc_movement()

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
            elif event.key == pygame.K_UP:
                # Changer d'étage vers le haut avec la flèche
                self._handle_arrow_floor_change(+1)
                return
            elif event.key == pygame.K_DOWN:
                # Changer d'étage vers le bas avec la flèche
                self._handle_arrow_floor_change(-1)
                return

        # Pour l'instant, gérer les entrées directement
        # TODO: Intégrer avec l'InputManager quand disponible
        pass
    
    def _handle_pause(self):
        """Gère la pause du jeu."""
        # La gestion de la pause est centralisée dans l'app; ne rien faire ici
        logger.debug("Pause handled by App")
    
    def update(self, dt):
        """Met à jour tous les systèmes."""
        if self.paused:
            return
        
        # Mettre à jour les systèmes world
        self._update_world_systems(dt)
        
        # Mettre à jour l'UI
        self._update_ui_systems(dt)
        
        # Mettre à jour le mouvement des NPCs
        self.npc_movement_manager.update(dt)

        # Générer des conversations aléatoires (seulement pour les NPCs en mouvement)
        if self.entity_manager:
            import time
            # Filtrer pour ne prendre que les NPCs en mouvement (pas les NPCs fixes)
            moving_npcs = []
            player = self.entity_manager.get_player()
            if player and hasattr(player, 'current_floor'):
                current_floor = player.current_floor
                for movement in self.npc_movement_manager.npc_movements.values():
                    npc = movement.npc
                    if hasattr(npc, 'current_floor') and npc.current_floor == current_floor:
                        moving_npcs.append(npc)

                if moving_npcs:
                    self.speech_bubbles.add_random_conversation(moving_npcs, time.time())

        # Gérer les interactions
        self._handle_interactions()
        
        # Vérifier les conditions de fin
        self._check_game_end_conditions()

        # Traiter les événements de timeline pilotés par l'heure
        self._process_timeline_events()

        # Hooks interruptions (toasts simples)
        # Abonnements posés en enter; ici rien de plus

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
        self.speech_bubbles.update(dt)

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
        
        # 1) D'abord vérifier s'il y a un PNJ runtime proche
        npc = self._find_nearby_runtime_npc(player, max_dist_px=50)
        if npc:
            # Trouver l'objet d'étage correspondant pour récupérer les données
            if self.building:
                floor = self.building.get_floor(current_floor)
                if floor:
                    for obj_data in floor.objects:
                        if obj_data.get('kind') == 'npc':
                            props = obj_data.get('props', {})
                            npc_id = props.get('npc_id', obj_data.get('id'))
                            if npc_id == npc.id:
                                self._interact_with_floor_object(obj_data)
                                return

        # 2) Sinon chercher des objets du nouveau système sur l'étage actuel
        if self.building:
            floor = self.building.get_floor(current_floor)
            if floor:
                nearby_object = self._find_nearby_floor_object(player_pos, floor.objects)
                if nearby_object:
                    self._interact_with_floor_object(nearby_object)
                    return
        
        # 3) Fallback vers le système legacy
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
        player_x = player_pos[0]
        
        # 1) ignorer les "npc" (ils servent de spawner, pas d'objet interactif)
        for obj_data in objects_list:
            if obj_data.get('kind') == 'npc':
                continue
            obj_x = obj_data.get('x', 0)
            if abs(player_x - obj_x) < 50:
                return obj_data
        return None

    def _find_nearby_runtime_npc(self, player, max_dist_px=50):
        """
        Trouve le PNJ runtime le plus proche du joueur sur le même étage.

        Args:
            player: Le joueur
            max_dist_px: Distance maximale en pixels

        Returns:
            PNJ runtime le plus proche ou None
        """
        if not hasattr(self, "runtime_npcs"):
            return None

        floor = player.current_floor
        best = None
        best_d = 1e9

        for npc in self.runtime_npcs.values():
            if getattr(npc, "current_floor", None) != floor:
                continue
            d = abs(player.x - getattr(npc, "x", 0))
            if d < best_d and d <= max_dist_px:
                best = npc
                best_d = d

        return best
    
    def _interact_with_floor_object(self, obj_data):
        """
        Interagit avec un objet du nouveau système.
        
        Args:
            obj_data: Données de l'objet depuis floors.json
        """
        kind = obj_data.get('kind', 'unknown')
        obj_id = obj_data.get('id', 'unknown')
        props = obj_data.get('props', {})
        
        # Récupérer la position du joueur pour les bulles
        if self.entity_manager:
            player = self.entity_manager.get_player()
            player_pos = player.get_position() if player else (400, 300)
        else:
            player_pos = (400, 300)

        if kind == "npc":
            name = props.get('name', 'Inconnu')
            dialogue_key = props.get('dialogue_key', '')
            npc_id = props.get('npc_id', obj_id)

            # ➊ Prendre d'abord le PNJ runtime classique
            npc_obj = self._get_runtime_npc(npc_id)
            
            # ➋ Sinon, tenter le PNJ fixe enregistré par le manager
            if not npc_obj and hasattr(self.npc_movement_manager, "static_npcs"):
                npc_obj = self.npc_movement_manager.static_npcs.get(npc_id)

            if not npc_obj:
                self.notification_manager.add_notification("...il n'y a personne ici.", 1.5)
                return

            # Tâche du boss / dialogue JSON en BULLES
            if self.task_manager:
                task = self.task_manager.get_task_for_npc(npc_id)
                if task and self.task_manager.is_task_available(task.id):
                    if self.task_manager.complete_task(task.id):
                        self.notification_manager.add_notification(f"Tâche terminée : {task.title}", 3.0)
                        self._play_sound("ui_click")

                        # CHAÎNAGE boss: après M1 -> offrir "chat_with_alex"
                        if npc_id == "boss_reed" and task.id == "M1":
                            self.task_manager.offer_task("chat_with_alex")
                        return

                    # CHAÎNAGE boss: après M4 -> offrir M5 "Salle prête pour 9h"
                    if npc_id == "boss_reed" and task.id == "M4":
                        self.task_manager.offer_task("M5")
                        self.speech_bubbles.speak_from_dict(self.strings, ["dialogues", "boss_m5"], npc_obj, color=(200, 200, 255))
                        return

            # Dialogues conditionnels selon l'état des tâches
            if npc_id == "boss_reed" and self.task_manager:
                if not self.task_manager.is_task_completed("M1"):
                    # première rencontre
                    self.speech_bubbles.speak_from_dict(self.strings, ["dialogues", "boss_reed"], npc_obj, color=(200, 200, 255))
                elif not self.task_manager.is_task_completed("M3"):
                    # M1 fait, M3 pas encore
                    self.speech_bubbles.speak_from_dict(self.strings, ["dialogues", "boss_reed_after_M1"], npc_obj, color=(200, 200, 255))
                else:
                    # M3 fait → nouveau texte de félicitations
                    self.speech_bubbles.speak_from_dict(self.strings, ["dialogues", "boss_reed_after_M3"], npc_obj, color=(200, 255, 200))
                return

            # PNJ Alex : petit retour après M3
            if npc_id == "alex" and self.task_manager and self.task_manager.is_task_completed("M3"):
                self.speech_bubbles.add_bubble("Nickel, la compta te remercie.", npc_obj, 2.5, (200, 255, 200))
                return

            # PNJ Alex : offrir S17 "Photocopies express" si pas encore offerte
            if npc_id == "alex" and self.task_manager and not self.task_manager.is_task_known("S17"):
                self.task_manager.offer_task("S17")
                self.speech_bubbles.speak_from_dict(self.strings, ["dialogues", "alex_copies"], npc_obj, color=(200, 200, 255))
                return

            # Agent de sécurité : logique badge cohérente
            if npc_id == "guard" and self.task_manager:
                # 1) offrir la collecte du badge si pas encore offerte
                if not self.task_manager.is_task_known("S6"):
                    self.task_manager.offer_task("S6")  # "Badge perdu" (ramasser)
                # 2) si le joueur porte déjà le badge, offrir la remise
                if "has_badge" in self.flags and not self.task_manager.is_task_known("S6b"):
                    self.task_manager.offer_task("S6b")  # "Remettre le badge"
                # 3) petite bulle
                self.speech_bubbles.speak_from_dict(self.strings, ["dialogues", "guard_badge"], npc_obj, color=(200, 200, 255))
                return

            # PNJ Maya : dialogue spécial pour les tasses
            if npc_id == "maya" and self.task_manager:
                # Si le joueur a des tasses à livrer (S15)
                if "mugs_collected" in self.flags:
                    self.speech_bubbles.speak_from_dict(self.strings, ["dialogues", "maya_mugs"], npc_obj, color=(200, 200, 255))
                    return

            # Fallback: dialogues JSON classiques
            key = dialogue_key or self._infer_dialogue_key_from_name(name)
            if key and "dialogues" in self.strings and key in self.strings["dialogues"]:
                self.speech_bubbles.speak_from_dict(self.strings, ["dialogues", key], npc_obj, color=(200, 200, 255))
            else:
                phrase = random.choice(self.speech_bubbles.random_phrases)
                self.speech_bubbles.add_bubble(phrase, npc_obj, 3.0, (200, 200, 255))
            return

        elif kind in ["plant", "papers", "printer", "reception", "coffee", "water", "receptionist", "desk", "trash", "pickup", "meeting", "window", "supply", "stapler", "cables", "mug", "sink", "copier", "vents", "whiteboard"]:
            # Interaction avec objet - nouveau système avec actions
            interactable_id = obj_id

            if interactable_id and self.task_manager:
                # Vérifier si la tâche est disponible pour cet objet
                task = self.task_manager.get_task_for_interactable(interactable_id)
                if task and self.task_manager.is_task_available(task.id):
                    # Récupérer l'action depuis les propriétés de la tâche
                    action = getattr(task, 'action', 'interact')

                    # Traiter selon l'action
                    if action == "collect":
                        if hasattr(task, 'gives_flag') and task.gives_flag:
                            self.flags.add(task.gives_flag)
                            self.speech_bubbles.add_bubble("C'est bon.", self.entity_manager.get_player(), 1.8, (200, 255, 200))
                        self.task_manager.complete_task(task.id)
                        self.notification_manager.add_notification(f"Tâche terminée : {task.title}", 3.0)
                        return

                    elif action == "collect_multi":
                        # Gérer la collecte multiple (papers_97_*)
                        if hasattr(self.task_manager, 'increment_counter'):
                            self.task_manager.increment_counter(task.id, 1)
                        else:
                            # Fallback simple
                            pass
                        self.speech_bubbles.add_bubble("Encore quelques pages...", self.entity_manager.get_player(), 1.6, (220, 220, 255))
                        if hasattr(self.task_manager, 'is_goal_reached') and self.task_manager.is_goal_reached(task.id):
                            if hasattr(task, 'gives_flag') and task.gives_flag:
                                self.flags.add(task.gives_flag)
                            self.notification_manager.add_notification("Papiers ramassés", 2.0)
                            self.task_manager.complete_task(task.id)
                        return

                    elif action == "deliver":
                        if hasattr(task, 'needs_flag') and task.needs_flag and task.needs_flag not in self.flags:
                            self.speech_bubbles.add_bubble("Il me manque quelque chose...", self.entity_manager.get_player(), 1.8, (255, 200, 200))
                            return
                        if hasattr(task, 'clears_flag') and task.clears_flag:
                            self.flags.discard(task.clears_flag)
                        self.task_manager.complete_task(task.id)
                        self.speech_bubbles.add_bubble("Parfait.", self.entity_manager.get_player(), 1.8, (200, 255, 200))
                        self.notification_manager.add_notification(f"Tâche terminée : {task.title}", 3.0)
                        return

                    elif action == "interact" and hasattr(task, 'needs_flag'):
                        if task.needs_flag and task.needs_flag not in self.flags:
                            self.speech_bubbles.add_bubble("Je dois d'abord prendre de l'eau.", self.entity_manager.get_player(), 2.0, (255, 200, 200))
                            return
                        # Consommer l'eau pour arroser
                        if hasattr(task, 'needs_flag') and task.needs_flag:
                            self.flags.discard(task.needs_flag)
                        self.task_manager.complete_task(task.id)
                        self.speech_bubbles.add_bubble("Ça fait du bien aux feuilles.", self._get_runtime_npc("alex") or self.entity_manager.get_player(), 2.0, (200, 255, 200))
                        self.notification_manager.add_notification(f"Tâche terminée : {task.title}", 3.0)
                        return

                    elif action == "inspect":
                        self.task_manager.complete_task(task.id)
                        self.speech_bubbles.add_bubble("Tout semble en ordre.", self.entity_manager.get_player(), 2.0, (200, 200, 255))
                        self.notification_manager.add_notification(f"Tâche terminée : {task.title}", 3.0)
                        return

                    elif action == "linger":
                        # Action spéciale pour prendre du temps à la fenêtre
                        linger_seconds = getattr(task, 'linger_seconds', 10)
                        self.task_manager.complete_task(task.id)
                        self.speech_bubbles.add_bubble(f"Un moment de détente... ({linger_seconds}s)", self.entity_manager.get_player(), linger_seconds, (150, 200, 255))
                        self.notification_manager.add_notification(f"Tâche terminée : {task.title}", 3.0)
                        return

                    else:
                        # Action par défaut (interact)
                        success = self.task_manager.complete_task(task.id)
                        if success:
                            self.notification_manager.add_notification(f"Tâche terminée : {task.title}", 3.0)

                            # Messages spécifiques selon le type avec sons et bulles
                            if kind == "plant":
                                self.notification_manager.add_notification("Plante arrosée !", 2.0)
                                self._bubble_player("*glou glou*", 1.5, (100, 255, 100))
                                self._play_sound("water_plant")
                            elif kind == "papers":
                                self.notification_manager.add_notification("Papiers rangés !", 2.0)
                                self._bubble_player("Tout bien rangé !", 2.0, (255, 255, 100))
                                self._play_sound("paper_pickup")
                            elif kind == "printer":
                                self.notification_manager.add_notification("Imprimante réparée !", 2.0)
                                self._bubble_player("*vrrrr* Ça marche !", 2.0, (100, 200, 255))
                                self._play_sound("printer_sound")
                            elif kind == "reception":
                                self.notification_manager.add_notification("Badge récupéré !", 2.0)
                                self._bubble_player("Badge en poche !", 2.0, (255, 200, 100))
                                self._play_sound("ui_click")
                            elif kind == "coffee":
                                self.notification_manager.add_notification("Café pris !", 2.0)
                                self._bubble_player("Mmmh, délicieux !", 2.0, (139, 69, 19))
                                self._play_sound("coffee_sip")
                            elif kind == "water":
                                self.notification_manager.add_notification("Plantes arrosées !", 2.0)
                                self._bubble_player("Toutes les plantes sont hydratées !", 2.5, (100, 255, 100))
                                self._play_sound("water_plant")
                            elif kind == "receptionist":
                                self.notification_manager.add_notification("Accueil aidé !", 2.0)
                                self._bubble_player("Service rendu !", 2.0, (255, 150, 255))
                                self._play_sound("ui_click")
                            elif kind == "desk":
                                self.notification_manager.add_notification("Bureau organisé !", 2.0)
                                self._bubble_player("Bureau impeccable !", 2.0, (200, 200, 200))
                                self._play_sound("paper_pickup")
                        else:
                            self.notification_manager.add_notification("Tâche déjà terminée.", 2.0)
                else:
                    # Tâche non disponible : bloquer l'action et donner un indice contextuel
                    hint = None
                    if kind == "plant":
                        # si la tâche arrosage (S1) est lock, c'est qu'il faut de l'eau
                        hint = "Je devrais d'abord remplir une bouteille."
                    elif kind in ("trash",):
                        hint = "Je n'ai rien à déposer."
                    elif kind in ("printer",):
                        hint = "Alex doit d'abord me briefer."
                    elif kind in ("coffee",):
                        hint = "Pas le moment."
                    elif kind in ("papers",):
                        hint = "On me demandera peut-être de les trier."
                    elif kind in ("pickup",):
                        hint = "Pas maintenant."
                    elif kind in ("supply",):
                        hint = "Je devrais voir si quelqu'un a demandé quelque chose."
                    elif kind in ("stapler",):
                        hint = "Il me faut des agrafes."
                    elif kind in ("copier",):
                        hint = "On m'a demandé un dossier ?"
                    elif kind in ("vents",):
                        hint = "Juste un coup d'œil."
                    elif kind in ("whiteboard",):
                        hint = "Je peux le nettoyer rapidement."
                    elif kind in ("mug",):
                        hint = "Ces tasses s'accumulent..."
                    elif kind in ("sink",):
                        hint = "Je n'ai rien à laver."
                    elif kind in ("cables",):
                        hint = "Ces câbles traînent."
                    else:
                        hint = None

                    if hint:
                        # bulle au joueur plutôt qu'un toast "tâche indisponible"
                        self.speech_bubbles.add_bubble(hint, self.entity_manager.get_player(), 1.8, (220, 220, 220))
                    # on ne déclenche rien
                    return
            else:
                # Interaction simple sans tâche
                messages = {
                    "plant": "Vous regardez la plante.",
                    "papers": "Des papiers éparpillés.",
                    "printer": "L'imprimante ronronne.",
                    "reception": "Le bureau d'accueil.",
                    "coffee": "Une machine à café.",
                    "water": "Un distributeur d'eau.",
                    "receptionist": "La réceptionniste.",
                    "desk": "Votre bureau.",
                    "trash": "Une poubelle.",
                    "pickup": "Un objet au sol.",
                    "meeting": "Une salle de réunion.",
                    "window": "Une belle vue."
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
                    self._change_player_floor(floor_number)
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
        if self.game_clock and self.game_clock.is_deadline():
            logger.info("Game deadline reached, transitioning to summary")
            try:
                screen = pygame.display.get_surface()
                if screen:
                    # Effet de shake simplifié
                    self.shake_screen(screen, duration=0.5, intensity=8)
                    # Transition fade simple
                    self._fade_up(screen, duration_ms=800, color=(0, 0, 0))
                    # Vidéo finale si disponible
                    if MOVIEPY_AVAILABLE:
                        self.play_final_video(screen)
            except Exception as e:
                logger.error(f"Error during end transition: {e}")
            finally:
                # Toujours passer au résumé même en cas d'erreur
                stats = self._gather_session_stats()
                self.switch_to("summary", stats=stats)

    def _fade_up(self, screen, duration_ms=900, color=(0, 0, 0)):
        """Transition fade up (noir qui monte du bas vers le haut)."""
        try:
            W, H = screen.get_size()
            clock = pygame.time.Clock()
            t0 = pygame.time.get_ticks()
            running = True
            while running:
                t = (pygame.time.get_ticks() - t0) / duration_ms
                if t >= 1.0:
                    t = 1.0
                    running = False
                h = int(H * t)
                overlay = pygame.Surface((W, h))
                overlay.fill(color)
                screen.blit(overlay, (0, H - h))
                pygame.display.flip()
                clock.tick(60)
        except Exception as e:
            logger.error(f"Error during fade transition: {e}")

    def shake_screen(self, screen, duration=0.7, intensity=12):
        """Effet de tremblement sur tout l'écran avant la vidéo de fin."""
        try:
            clock = pygame.time.Clock()
            start = time.time()
            original = screen.copy()
            while time.time() - start < duration:
                offset_x = int((pygame.time.get_ticks() % intensity) - intensity // 2)
                offset_y = int((pygame.time.get_ticks() * 1.5 % intensity) - intensity // 2)
                screen.fill((0, 0, 0))
                screen.blit(original, (offset_x, offset_y))
                pygame.display.flip()
                clock.tick(60)
        except Exception as e:
            logger.error(f"Error during screen shake: {e}")

    def play_final_video(self, screen):
        """Joue la vidéo finale avant le résumé."""
        if not MOVIEPY_AVAILABLE:
            logger.warning("MoviePy not available, skipping final video")
            return

        try:
            video_path = os.path.join("assets", "final.mp4")
            if not os.path.exists(video_path):
                logger.warning(f"Final video not found at {video_path}")
                return

            clip = mpy.VideoFileClip(video_path)
            for frame in clip.iter_frames(fps=24, dtype="uint8"):
                surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
                surf = pygame.transform.scale(surf, (WIDTH, HEIGHT))
                screen.blit(surf, (0, 0))
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return
                time.sleep(1 / 24)
            clip.close()
        except Exception as e:
            logger.error(f"Error playing final video: {e}")

    def draw(self, screen):
        """Dessine la scène."""
        # Fond noir
        screen.fill((0, 0, 0))
        
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
        floor_height = HEIGHT // 3  # Chaque étage prend exactement 1/3 de l'écran
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
            
            # Position Y à l'écran : étages collés sans espace
            screen_y = i * floor_height
            
            # 1. Dessiner le sprite d'étage complet (couvre toute la largeur, inclut ascenseur)
            floor_sprite = self._get_floor_sprite(floor_num)
            if floor_sprite:
                # Redimensionner pour couvrir exactement la hauteur d'étage sans espaces
                # Calculer le ratio pour maintenir les proportions
                sprite_ratio = floor_sprite.get_width() / floor_sprite.get_height()
                screen_ratio = WIDTH / floor_height

                # Forcer la hauteur exacte pour éviter les espaces
                scaled_height = floor_height
                scaled_width = int(floor_height * sprite_ratio)

                # Redimensionner le sprite
                floor_scaled = pygame.transform.scale(floor_sprite, (scaled_width, scaled_height))

                # Aligner à gauche (comme l'ascenseur) - la droite peut s'étendre indéfiniment
                x_offset = 0
                screen.blit(floor_scaled, (x_offset, screen_y))
            else:
                # Fallback : fond par défaut
                floor_rect = pygame.Rect(0, screen_y, WIDTH, floor_height)
                color = (240, 240, 240) if floor_num == current_floor else (200, 200, 200)
                pygame.draw.rect(screen, color, floor_rect)

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
            
            # 2. Dessiner les objets de l'étage (nouveau système)
            for obj_data in floor.objects:
                self._draw_floor_object(screen, obj_data, screen_y, floor_height)
            
            # 3. Dessiner le joueur s'il est sur cet étage
            if floor_num == current_floor and self.entity_manager:
                player = self.entity_manager.get_player()
                if player:
                    player_sprite = asset_manager.get_image("player_idle")
                    # Utiliser la taille définie dans le manifest (pas de redimensionnement automatique)
                    # Le sprite est déjà redimensionné par l'AssetManager selon assets_manifest.json
                    player_x = player.x - player_sprite.get_width() // 2
                    # Positionner le joueur au sol avec baseline cohérente
                    baseline_y = screen_y + floor_height - 1
                    player_y = baseline_y - player_sprite.get_height()
                    screen.blit(player_sprite, (player_x, player_y))

                    # Ancre pour les bulles (au sommet de la tête, centré)
                    player._bubble_anchor_x = player_x + player_sprite.get_width() // 2
                    player._bubble_anchor_y = player_y

            # 4. Dessiner les objets interactifs legacy (compatibilité) - sur tous les étages
            if self.entity_manager:
                # Objets interactifs legacy
                for obj in self.entity_manager.interactables.values():
                    if getattr(obj, 'current_floor', current_floor) == floor_num:
                        self._draw_legacy_object(screen, obj, screen_y, floor_height)

            # 5. Dessiner les NPCs en mouvement (nouveau système)
            for movement in self.npc_movement_manager.npc_movements.values():
                npc = movement.npc
                if hasattr(npc, 'current_floor') and npc.current_floor == floor_num:
                    # Utiliser le sprite approprié
                    sprite_key = getattr(npc, 'sprite_key', 'npc_generic')
                    npc_sprite = asset_manager.get_image(sprite_key)
                    npc_x = npc.x - npc_sprite.get_width() // 2
                    # Positionner le NPC au sol avec baseline cohérente
                    baseline_y = screen_y + floor_height - 1
                    npc_y = baseline_y - npc_sprite.get_height()
                    screen.blit(npc_sprite, (npc_x, npc_y))

                    # Ancre pour les bulles (au sommet de la tête, centré)
                    npc._bubble_anchor_x = npc_x + npc_sprite.get_width() // 2
                    npc._bubble_anchor_y = npc_y

            # 5b. Dessiner les PNJ FIXES (boss, réception, etc.)
            for npc in getattr(self.npc_movement_manager, "static_npcs", {}).values():
                if hasattr(npc, 'current_floor') and npc.current_floor == floor_num:
                    sprite_key = getattr(npc, 'sprite_key', 'npc_generic')
                    npc_sprite = asset_manager.get_image(sprite_key)
                    npc_x = npc.x - npc_sprite.get_width() // 2
                    baseline_y = screen_y + floor_height - 1
                    npc_y = baseline_y - npc_sprite.get_height()
                    screen.blit(npc_sprite, (npc_x, npc_y))
                    npc._bubble_anchor_x = npc_x + npc_sprite.get_width() // 2
                    npc._bubble_anchor_y = npc_y

    def _draw_floor_object(self, screen, obj_data: dict, screen_y: int, floor_height: int) -> None:
        """
        Dessine un objet positionné sur un étage.
        
        Args:
            screen: Surface de rendu
            obj_data: Données de l'objet depuis floors.json
            screen_y: Position Y de l'étage à l'écran
            floor_height: Hauteur d'un étage
        """
        from src.core.assets import asset_manager
        
        kind = obj_data.get("kind", "unknown")
        # IMPORTANT : ne JAMAIS dessiner les PNJ ici, ils sont rendus par le manager de mouvement
        if kind == "npc":
            return

        obj_x = obj_data.get("x", 0)
        obj_y = obj_data.get("y", 0)
        props = obj_data.get("props", {})
        
        # Calculer la position à l'écran (objets posés au sol)
        # Les objets sont maintenant positionnés par rapport à la largeur complète de l'écran
        screen_obj_x = obj_x
        
        # Choisir le sprite selon le kind
        sprite_key = self._get_sprite_key_for_kind(kind, props)
        if sprite_key:
            obj_sprite = asset_manager.get_image(sprite_key)
            
            # Positionner l'objet au sol avec baseline cohérente
            final_x = screen_obj_x - obj_sprite.get_width() // 2
            baseline_y = screen_y + floor_height - 1

            # Positionnement uniforme selon le type d'objet
            if kind in ["plant", "printer", "desk", "coffee"]:
                # Objets volumineux posés sur le sol
                final_y = baseline_y - obj_sprite.get_height()
            elif kind in ["papers", "water"]:
                # Petits objets posés sur le sol (léger écrasement visuel)
                final_y = baseline_y - obj_sprite.get_height() - 2
            else:
                # Objets par défaut
                final_y = baseline_y - obj_sprite.get_height()
            
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

            # Ancre pour les bulles (au sommet de l'objet)
            obj_data['_bubble_anchor_x'] = final_x + obj_sprite.get_width() // 2
            obj_data['_bubble_anchor_y'] = final_y

            # Debug visuel désactivé pour le joueur
            # pygame.draw.circle(screen, (255, 0, 0, 50), (int(screen_obj_x), int(final_y + obj_sprite.get_height()//2)), 50, 2)

    def _get_floor_sprite(self, floor_num: int):
        """
        Récupère le sprite d'étage pour un numéro d'étage donné.

        Args:
            floor_num: Numéro d'étage

        Returns:
            Surface du sprite d'étage ou None si non trouvé
        """
        from src.core.assets import asset_manager

        # Utiliser le nouveau sprite d'étage complet qui inclut l'ascenseur
        try:
            # Utiliser get_background pour les sprites d'étage
            if hasattr(asset_manager, 'get_background'):
                return asset_manager.get_background("floor_complete")
            else:
                return asset_manager.get_image("floor_complete")
        except:
            pass

        # Fallback vers le sprite par défaut
        try:
            if hasattr(asset_manager, 'get_background'):
                return asset_manager.get_background("floor_default")
            else:
                return asset_manager.get_image("floor_default")
        except:
            return None

    def _get_sprite_key_for_kind(self, kind: str, props: Optional[dict] = None) -> str:
        """
        Retourne la clé de sprite pour un type d'objet donné.
        
        Args:
            kind: Type d'objet (plant, papers, npc, etc.)
            props: Propriétés de l'objet (peut contenir sprite_key)

        Returns:
            Clé de sprite dans le manifest
        """
        # Si c'est un NPC et qu'il a un sprite_key spécifique, l'utiliser
        if kind == "npc" and props and "sprite_key" in props:
            return props["sprite_key"]

        sprite_mapping = {
            "plant": "interactable_plant",
            "papers": "interactable_papers", 
            "printer": "interactable_printer",
            "npc": "npc_generic",
            "coffee": "coffee",
            "water": "water",
            "receptionist": "receptionist",
            "desk": "desk",
            "reception": "interactable_printer",  # Fallback
            "decoration": "interactable_plant",  # Fallback
            "lightbulb": "interactable_papers",  # Fallback
            "filing_cabinet": "interactable_printer",  # Fallback
            "server": "interactable_printer",  # Fallback
            "presentation": "interactable_papers",  # Fallback
            "phone": "interactable_papers",  # Fallback
            "boxes": "interactable_papers",  # Fallback
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

        # Bulles de conversation
        self.speech_bubbles.draw(screen)

    def _gather_session_stats(self) -> dict:
        """
        Agrège les statistiques de la session pour l'écran de résumé et les trophées.
        """
        stats = {}
        try:
            # Temps
            if self.game_clock:
                stats["time"] = {
                    "current": self.game_clock.get_time_str(),
                    "detailed": self.game_clock.get_detailed_time_str(),
                    "progress": self.game_clock.get_progress(),
                    "elapsed_real_seconds": self.game_clock.get_elapsed_real_time(),
                }
            # Tâches
            if self.task_manager:
                stats["tasks"] = self.task_manager.get_stats()
            # Bâtiment
            if self.building:
                stats["building"] = self.building.get_stats()
            # Ascenseur
            if self.elevator:
                stats["elevator"] = self.elevator.get_stats()
            # Entités et joueur
            if self.entity_manager:
                stats["entities"] = self.entity_manager.get_stats()
                player = self.entity_manager.get_player()
                if player:
                    stats["player"] = player.get_stats()
        except Exception as e:
            logger.error(f"Error gathering session stats: {e}")
        return stats

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
        
        # D'abord PNJ runtime
        npc = self._find_nearby_runtime_npc(player, max_dist_px=50)
        if npc:
            name = getattr(npc, "name", "Personne")
            self.hud.show_interaction_hint(f"E : Parler à {name}")
            return

        # Sinon objets d'étage (déjà filtrés)
        if self.building:
            floor = self.building.get_floor(current_floor)
            if floor:
                nearby_object = self._find_nearby_floor_object(player_pos, floor.objects)
                if nearby_object:
                    kind = nearby_object.get('kind', 'objet')
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
                    # Utiliser les flèches pour changer d'étage
                    self.hud.show_interaction_hint("↑/↓ : Changer d'étage")
                else:
                    self.hud.hide_interaction_hint()

    def _handle_arrow_floor_change(self, direction: int) -> None:
        """
        Change d'un étage dans la direction donnée si le joueur est près de l'ascenseur.

        Args:
            direction: +1 pour monter, -1 pour descendre
        """
        if not self.building or not self.entity_manager:
            return
        player = self.entity_manager.get_player()
        if not player:
            return
        # Vérifier proximité ascenseur
        elevator_x = 30 + 40
        if abs(player.x - elevator_x) >= 60:
            self.notification_manager.add_notification("Approchez-vous de l'ascenseur.", 1.5)
            return

        # Calculer nouvel étage borné aux étages existants
        current = player.current_floor
        all_floors = self.building.get_all_floors()
        if not all_floors:
            return
        if current not in all_floors:
            current = all_floors[0]
        try:
            idx = all_floors.index(current)
        except ValueError:
            idx = 0
        new_idx = max(0, min(len(all_floors) - 1, idx + (1 if direction > 0 else -1)))
        new_floor = all_floors[new_idx]

        if new_floor != current:
            self._change_player_floor(new_floor)
        else:
            # Déjà au bord
            self.notification_manager.add_notification("Pas d'autre étage dans cette direction.", 1.5)
    
    
    def exit(self):
        """Appelé en quittant la scène."""
        super().exit()
        
        # Désabonnements
        for (evt, handler) in self._subscriptions:
            try:
                # Pas de méthode unsubscribe dans EventBus minimal; ignorer
                pass
            except Exception:
                pass
        
        logger.info("Exited GameplayScene")

    # === Adapters: Time & Timeline ===
    def _subscribe_events(self) -> None:
        def on_tick(payload):
            self._on_time_tick(payload)
        def on_reached(payload):
            self._on_time_reached(payload)
        event_bus.subscribe(TIME_TICK, on_tick)
        event_bus.subscribe(TIME_REACHED, on_reached)
        self._subscriptions.append((TIME_TICK, on_tick))
        self._subscriptions.append((TIME_REACHED, on_reached))

        # Abonnement aux événements spécifiques de la timeline
        def on_printer_escalate(payload):
            self._printer_requirement = 3
        event_bus.subscribe("PRINTER_ESCALATE_IF_NOT_FIXED", on_printer_escalate)
        self._subscriptions.append(("PRINTER_ESCALATE_IF_NOT_FIXED", on_printer_escalate))

    def _on_time_tick(self, payload):
        # Espace réservé pour interruptions, mise à jour UI, etc.
        pass

    def _on_time_reached(self, payload):
        # Pour l'instant, rien ici; la TimelineController émet aussi des événements dédiés
        pass

    def _process_timeline_events(self):
        """
        Hook explicite (tests) pour appliquer des effets en fonction de l'heure.
        - 08:37: l'imprimante devient plus exigeante si non réglée.
        """
        try:
            if self.game_clock and self.game_clock.get_time_str() >= "08:37":
                self._printer_requirement = 3
        except Exception:
            pass

    def _setup_npc_movement(self) -> None:
        """Configure le mouvement des NPCs."""
        self.runtime_npcs.clear()
        if not self.building:
            return

        # Largeur jouable (paramètre de NPCMovement)
        floor_width = WIDTH

        for floor_num, floor in self.building.floors.items():
            for obj in floor.objects:
                if obj.get("kind") == "npc":
                    props = obj.get("props", {})
                    npc_id = props.get("npc_id", obj.get("id"))
                    if not npc_id:
                        continue

                    # Crée un petit objet PNJ runtime
                    npc = type("RuntimeNPC", (), {})()
                    npc.id = npc_id
                    npc.name = props.get("name", "NPC")
                    npc.x = float(obj.get("x", 200))
                    npc.y = 0.0  # on ne s'en sert pas, on blitte sur baseline
                    npc.current_floor = floor_num
                    npc.sprite_key = props.get("sprite_key", "npc_generic")

                    # Enregistre
                    self.runtime_npcs[npc_id] = npc

                    # Active le mouvement
                    self.npc_movement_manager.add_npc(npc, floor_width=floor_width)

        logger.info("NPC movement system configured")

    def _bubble_player(self, text, dur=2.0, color=(255,255,200)):
        """Helper pour créer une bulle du joueur."""
        player = self.entity_manager.get_player()
        if player:
            self.speech_bubbles.add_bubble(text, player, dur, color)

    def _infer_dialogue_key_from_name(self, name: str) -> Optional[str]:
        """Infère la clé de dialogue à partir du nom du NPC."""
        if not name:
            return None
        n = name.lower()
        if "boss" in n or "reed" in n:
            return "boss_morning"   # tu peux mettre "boss_reed" selon la scène voulue
        if "alex" in n:
            return "alex_morning"
        if "maya" in n:
            return "maya_morning"
        if "marie" in n:
            return "marie_morning"
        if "thomas" in n:
            return "thomas_morning"
        if "claire" in n:
            return "claire_morning"
        if "paul" in n:
            return "paul_morning"
        if "julien" in n:
            return "julien_morning"
        if "sarah" in n or "assistant" in n:
            return "assistant_morning"
        if "guard" in n or "sécurité" in n:
            return "guard_morning"
        return None

    def _get_runtime_npc(self, npc_id: str):
        """Récupère le PNJ runtime correspondant à un ID."""
        return self.runtime_npcs.get(npc_id)

    # === Adapters: DSL Effects ===
    def _play_sound(self, sound_key: str) -> None:
        """Joue un effet sonore."""
        try:
            from src.core.assets import asset_manager
            sound = asset_manager.get_sound(sound_key)
            if sound:
                sound.play()
        except Exception as e:
            logger.debug(f"Could not play sound {sound_key}: {e}")

    def _apply_effect(self, effect: dict) -> None:
        """Applique un effet simple: set_flag, offer_task, discover_task, complete_task, add_rep, toast."""
        if not isinstance(effect, dict):
            return
        try:
            if "set_flag" in effect:
                self.flags.add(effect["set_flag"])
                if effect["set_flag"] == "met_boss":
                    self._intro_lock_active = False
            elif "offer_task" in effect and self.task_manager:
                self.task_manager.offer_task(effect["offer_task"])
            elif "discover_task" in effect and self.task_manager:
                self.task_manager.discover_task(effect["discover_task"])
            elif "complete_task" in effect and self.task_manager:
                self.task_manager.complete_task(effect["complete_task"])
            elif "add_rep" in effect:
                # Réputation non implémentée: placeholder
                pass
            elif "toast" in effect:
                self.notification_manager.add_notification(str(effect["toast"]), 2.0)
        except Exception:
            pass