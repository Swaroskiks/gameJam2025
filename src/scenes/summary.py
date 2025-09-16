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
        
        # Simuler quelques trophées basés sur les stats (logique simplifiée)
        total_points = self.game_stats.get("total_points", 0)
        completed_tasks = self.game_stats.get("completed_tasks", 0)
        main_tasks_completed = self.game_stats.get("main_tasks_completed", 0)
        
        for trophy_data in self.trophies_data["trophies"]:
            earned = False
            
            # Logique simplifiée de trophées
            if trophy_data["id"] == "main_verte" and "water_plant" in str(self.game_stats):
                earned = True
            elif trophy_data["id"] == "ranger_pro" and "organize_papers" in str(self.game_stats):
                earned = True
            elif trophy_data["id"] == "employe_modele" and main_tasks_completed >= 3:
                earned = True
            elif trophy_data["id"] == "ponctuel" and completed_tasks > 0:
                earned = True
            
            if earned:
                self.earned_trophies.append(trophy_data)
        
        logger.info(f"Earned {len(self.earned_trophies)} trophies")
    
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
        
        # Stats
        stats_to_show = [
            ("Tâches terminées", self.game_stats.get("completed_tasks", 0)),
            ("Points obtenus", self.game_stats.get("total_points", 0)),
            ("Tâches principales", self.game_stats.get("main_tasks_completed", 0)),
            ("Tâches annexes", self.game_stats.get("side_tasks_completed", 0)),
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
