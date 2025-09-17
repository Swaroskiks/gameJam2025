"""
Scène de résumé final pour A Day at the Office.
Affiche les trophées, statistiques, et un message respectueux.
"""

import logging
import pygame
from src.core.scene_manager import Scene
from src.core.assets import asset_manager
from src.core.utils import load_json_safe, draw_text_centered
from src.settings import WIDTH, HEIGHT, UI_PANEL, UI_TEXT, UI_HOVER, DATA_PATH

logger = logging.getLogger(__name__)


class SummaryScene(Scene):
    """
    Scène de résumé final.
    
    Affiche les statistiques de la partie, les trophées obtenus,
    et un message de conclusion respectueux.
    """
    
    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        
        # Polices
        self.font_title = None
        self.font_subtitle = None
        self.font_body = None
        self.font_button = None
        
        # Données
        self.trophies_data = {}
        self.game_stats = {}
        self.earned_trophies = []
        
        # Bouton
        self.button_continue = pygame.Rect(WIDTH//2 - 100, HEIGHT - 80, 200, 50)
        self.hovered_button = False
        
        # Animation
        self.fade_in_time = 0.0
        self.fade_duration = 2.0
        
        logger.info("SummaryScene initialized")
    
    def enter(self, **kwargs):
        """Appelé en entrant dans la scène."""
        super().enter(**kwargs)
        
        # Récupérer les statistiques de jeu
        self.game_stats = kwargs.get('stats', {})
        
        # Charger les polices
        try:
            self.font_title = asset_manager.get_font("title_font")
            self.font_subtitle = asset_manager.get_font("ui_font")
            self.font_body = asset_manager.get_font("body_font")
            self.font_button = asset_manager.get_font("ui_font")
        except Exception as e:
            logger.error(f"Error loading fonts: {e}")
            # Fallback vers polices système
            self.font_title = pygame.font.SysFont(None, 36)
            self.font_subtitle = pygame.font.SysFont(None, 24)
            self.font_body = pygame.font.SysFont(None, 18)
            self.font_button = pygame.font.SysFont(None, 24)
        
        # Charger les données de trophées
        self._load_trophies_data()
        
        # Calculer les trophées obtenus
        self._calculate_earned_trophies()
        
        logger.info("Summary scene loaded with stats")
    
    def _load_trophies_data(self):
        """Charge les données de trophées."""
        try:
            trophies_path = DATA_PATH / "trophies.json"
            self.trophies_data = load_json_safe(trophies_path) or {}
            logger.debug("Trophies data loaded")
        except Exception as e:
            logger.error(f"Error loading trophies: {e}")
            self.trophies_data = {}
    
    def _calculate_earned_trophies(self):
        """Calcule les trophées obtenus basés sur les statistiques."""
        self.earned_trophies = []
        
        if not self.trophies_data.get("trophies"):
            return
        
        for trophy_data in self.trophies_data["trophies"]:
            condition = trophy_data.get("condition", {})
            if self._evaluate_trophy_condition(condition, self.game_stats):
                self.earned_trophies.append(trophy_data)
        
        logger.info(f"Earned {len(self.earned_trophies)} trophies")

    def _evaluate_trophy_condition(self, condition: dict, stats: dict) -> bool:
        """Évalue une condition de trophée contre les stats collectées."""
        try:
            ctype = condition.get("type")
            if not ctype:
                return False
            
            tasks_stats = (stats.get("tasks") or {})
            building_stats = (stats.get("building") or {})
            elevator_stats = (stats.get("elevator") or {})
            time_stats = (stats.get("time") or {})
            entities_stats = (stats.get("entities") or {})
            
            if ctype == "task_completed":
                task_id = condition.get("task_id")
                completed_ids = set(tasks_stats.get("completed_task_ids") or [])
                return bool(task_id) and task_id in completed_ids
            
            if ctype == "tasks_count":
                task_type = condition.get("task_type")
                min_count = int(condition.get("min_count", 0))
                by_type = tasks_stats.get("completed_by_type") or {}
                return by_type.get(task_type, 0) >= min_count
            
            if ctype == "all_main_tasks":
                return bool(tasks_stats.get("all_main_completed"))
            
            if ctype == "all_tasks":
                return bool(tasks_stats.get("all_completed"))
            
            if ctype == "floors_visited":
                min_floors = int(condition.get("min_floors", 0))
                return int(building_stats.get("visited_floors", 0)) >= min_floors
            
            if ctype == "time_limit":
                max_minutes = int(condition.get("max_minutes", 0))
                scope = condition.get("tasks", "main_tasks")
                # Critère: toutes les tâches du scope terminées ET temps réel sous la limite
                elapsed = float(time_stats.get("elapsed_real_seconds", 1e9))
                if scope == "main_tasks":
                    all_main = bool(tasks_stats.get("all_main_completed"))
                    return all_main and elapsed <= max_minutes * 60
                if scope == "all_tasks":
                    all_done = bool(tasks_stats.get("all_completed"))
                    return all_done and elapsed <= max_minutes * 60
                return False
            
            if ctype == "all_npcs_talked":
                # Non suivi précisément — retourner False par défaut
                return False
            
            if ctype == "elevator_uses":
                min_uses = int(condition.get("min_uses", 0))
                return int(elevator_stats.get("total_uses", 0)) >= min_uses
            
            if ctype in ("tasks_same_floor", "task_in_final_minutes", "tasks_in_floor_order", "help_per_floor"):
                # Non supporté pour l'instant
                return False
            
            return False
        except Exception as e:
            logger.error(f"Error evaluating trophy condition: {e}")
            return False
    
    def handle_event(self, event):
        """Gère les événements."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered_button = self.button_continue.collidepoint(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.button_continue.collidepoint(event.pos):
                self._handle_continue()
        
        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE]:
                self._handle_continue()
    
    def _handle_continue(self):
        """Retourne au menu principal."""
        logger.info("Returning to menu from summary")
        self.switch_to("menu")
    
    def update(self, dt):
        """Met à jour la scène."""
        self.fade_in_time += dt
    
    def draw(self, screen):
        """Dessine la scène."""
        # Fond sombre
        screen.fill((20, 20, 30))
        
        # Calculer l'alpha pour le fade-in
        alpha = min(255, int((self.fade_in_time / self.fade_duration) * 255))
        
        # Panneau principal
        panel_width = WIDTH - 100
        panel_height = HEIGHT - 100
        panel_rect = pygame.Rect(50, 50, panel_width, panel_height)
        
        # Fond du panneau avec alpha
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_color = (*UI_PANEL[:3], min(UI_PANEL[3], alpha))
        panel_surface.fill(panel_color)
        screen.blit(panel_surface, panel_rect.topleft)
        
        # Bordure
        border_color = (*UI_TEXT, alpha)
        if alpha > 50:  # Éviter les bordures trop faibles
            pygame.draw.rect(screen, UI_TEXT, panel_rect, 2)
        
        # Contenu avec alpha
        self._draw_content(screen, panel_rect, alpha)
    
    def _draw_content(self, screen, panel_rect, alpha):
        """
        Dessine le contenu du résumé.
        
        Args:
            screen: Surface de destination
            panel_rect: Rectangle du panneau
            alpha: Valeur alpha pour le fade-in
        """
        text_color = (*UI_TEXT, alpha)
        y_offset = panel_rect.y + 30
        
        # Titre principal
        if self.font_title and alpha > 100:
            self._draw_text_with_alpha(screen, "Résumé de votre journée", 
                                     self.font_title, text_color, 
                                     (WIDTH // 2, y_offset))
            y_offset += 60
        
        # Message contextuel
        if self.font_body and alpha > 150:
            context_lines = [
                "Il est maintenant 08:48.",
                "Votre journée de travail s'arrête ici.",
                "",
                "Merci d'avoir pris le temps de vivre ces petits moments,",
                "ces gestes ordinaires qui composent nos vies."
            ]
            
            for line in context_lines:
                if line.strip():
                    self._draw_text_with_alpha(screen, line, self.font_body, 
                                             text_color, (WIDTH // 2, y_offset))
                y_offset += 25
            
            y_offset += 20
        
        # Statistiques
        if alpha > 200:
            y_offset = self._draw_statistics(screen, y_offset, text_color)
            y_offset += 30
        
        # Trophées
        if alpha > 250:
            y_offset = self._draw_trophies(screen, y_offset, text_color)
        
        # Bouton continuer
        if alpha > 200:
            self._draw_continue_button(screen, alpha)
    
    def _draw_statistics(self, screen, y_start, text_color):
        """
        Dessine les statistiques de jeu.
        
        Args:
            screen: Surface de destination
            y_start: Position Y de départ
            text_color: Couleur du texte
            
        Returns:
            Nouvelle position Y
        """
        if not self.font_subtitle or not self.font_body:
            return y_start
        
        y_offset = y_start
        
        # Titre section
        self._draw_text_with_alpha(screen, "Statistiques", self.font_subtitle, 
                                 text_color, (WIDTH // 2, y_offset))
        y_offset += 35
        
        # Stats - récupérer depuis les stats des tâches
        tasks_stats = self.game_stats.get("tasks", {})
        stats_to_show = [
            ("Tâches terminées", tasks_stats.get("completed_tasks", 0)),
            ("Points obtenus", tasks_stats.get("total_points", 0)),
            ("Tâches principales", tasks_stats.get("main_tasks_completed", 0)),
            ("Tâches annexes", tasks_stats.get("side_tasks_completed", 0)),
            ("Progression générale", f"{int(tasks_stats.get('completion_percentage', 0) * 100)}%"),
        ]
        
        for label, value in stats_to_show:
            stat_text = f"{label}: {value}"
            self._draw_text_with_alpha(screen, stat_text, self.font_body, 
                                     text_color, (WIDTH // 2, y_offset))
            y_offset += 22
        
        return y_offset
    
    def _draw_trophies(self, screen, y_start, text_color):
        """
        Dessine les trophées obtenus.
        
        Args:
            screen: Surface de destination
            y_start: Position Y de départ
            text_color: Couleur du texte
            
        Returns:
            Nouvelle position Y
        """
        if not self.font_subtitle or not self.font_body:
            return y_start
        
        y_offset = y_start
        
        # Titre section
        trophy_count = len(self.earned_trophies)
        title = f"Trophées obtenus ({trophy_count})"
        self._draw_text_with_alpha(screen, title, self.font_subtitle, 
                                 text_color, (WIDTH // 2, y_offset))
        y_offset += 35
        
        # Trophées
        if self.earned_trophies:
            for trophy in self.earned_trophies[:5]:  # Limiter à 5 pour l'espace
                trophy_text = f"{trophy.get('icon', '🏆')} {trophy.get('name', 'Trophée')}"
                self._draw_text_with_alpha(screen, trophy_text, self.font_body, 
                                         text_color, (WIDTH // 2, y_offset))
                y_offset += 25
        else:
            self._draw_text_with_alpha(screen, "Aucun trophée obtenu cette fois.", 
                                     self.font_body, text_color, (WIDTH // 2, y_offset))
            y_offset += 25
        
        return y_offset
    
    def _draw_continue_button(self, screen, alpha):
        """
        Dessine le bouton continuer.
        
        Args:
            screen: Surface de destination
            alpha: Valeur alpha
        """
        # Couleur selon l'état
        if self.hovered_button:
            color = (*UI_HOVER[:3], min(UI_HOVER[3], alpha))
            border_width = 3
        else:
            color = (*UI_PANEL[:3], min(UI_PANEL[3], alpha))
            border_width = 2
        
        # Fond du bouton
        button_surface = pygame.Surface((self.button_continue.width, self.button_continue.height), pygame.SRCALPHA)
        button_surface.fill(color)
        screen.blit(button_surface, self.button_continue.topleft)
        
        # Bordure
        if alpha > 100:
            pygame.draw.rect(screen, UI_TEXT, self.button_continue, border_width)
        
        # Texte
        if self.font_button and alpha > 150:
            text_color = (*UI_TEXT, alpha)
            self._draw_text_with_alpha(screen, "Continuer", self.font_button, 
                                     text_color, self.button_continue.center)
    
    def _draw_text_with_alpha(self, screen, text, font, color, center_pos):
        """
        Dessine du texte avec transparence.
        
        Args:
            screen: Surface de destination
            text: Texte à dessiner
            font: Police à utiliser
            color: Couleur avec alpha (R, G, B, A)
            center_pos: Position du centre
        """
        # Créer la surface de texte
        text_surface = font.render(text, True, color[:3])  # RGB seulement
        
        # Appliquer l'alpha si nécessaire
        if len(color) > 3:
            text_surface.set_alpha(color[3])
        
        # Centrer et dessiner
        text_rect = text_surface.get_rect(center=center_pos)
        screen.blit(text_surface, text_rect)
