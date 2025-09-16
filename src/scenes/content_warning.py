"""
Scène d'avertissement de contenu pour A Day at the Office.
Informe respectueusement le joueur du contexte historique.
"""

import logging
import pygame
from src.core.scene_manager import Scene
from src.core.assets import asset_manager
from src.settings import WIDTH, HEIGHT, UI_PANEL, UI_TEXT, UI_HOVER
from src.core.utils import draw_text_centered

logger = logging.getLogger(__name__)


class ContentWarningScene(Scene):
    """
    Scène d'avertissement de contenu.
    
    Affiche un avertissement respectueux sur le contexte historique
    avant de permettre au joueur de continuer.
    """
    
    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        
        # Polices
        self.font_title = None
        self.font_body = None
        self.font_button = None
        
        # Boutons
        self.button_understand = pygame.Rect(WIDTH//2 - 100, HEIGHT - 120, 200, 50)
        self.button_back = pygame.Rect(WIDTH//2 - 100, HEIGHT - 60, 200, 50)
        
        # État
        self.hovered_button = None
        
        # Contenu
        self.warning_lines = [
            "Ce jeu évoque les événements du 11 septembre 2001",
            "dans le World Trade Center de manière respectueuse.",
            "",
            "Il ne contient aucune représentation graphique",
            "des événements tragiques.",
            "",
            "Le jeu s'arrête à 08:48 et se concentre sur",
            "les petits gestes du quotidien."
        ]
        
        logger.info("ContentWarningScene initialized")
    
    def enter(self, **kwargs):
        """Appelé en entrant dans la scène."""
        super().enter(**kwargs)
        
        # Charger les polices
        try:
            self.font_title = asset_manager.get_font("title_font")
            self.font_body = asset_manager.get_font("body_font")
            self.font_button = asset_manager.get_font("ui_font")
        except Exception as e:
            logger.error(f"Error loading fonts: {e}")
            # Fallback vers polices système
            self.font_title = pygame.font.SysFont(None, 36)
            self.font_body = pygame.font.SysFont(None, 18)
            self.font_button = pygame.font.SysFont(None, 24)
        
        logger.debug("Entered ContentWarningScene")
    
    def handle_event(self, event):
        """Gère les événements."""
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            
            # Vérifier quel bouton est survolé
            if self.button_understand.collidepoint(mouse_pos):
                self.hovered_button = "understand"
            elif self.button_back.collidepoint(mouse_pos):
                self.hovered_button = "back"
            else:
                self.hovered_button = None
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche
                if self.button_understand.collidepoint(event.pos):
                    self._handle_understand()
                elif self.button_back.collidepoint(event.pos):
                    self._handle_back()
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._handle_understand()
            elif event.key == pygame.K_ESCAPE:
                self._handle_back()
    
    def _handle_understand(self):
        """Gère le bouton 'J'ai compris'."""
        logger.info("User acknowledged content warning")
        self.switch_to("menu")
    
    def _handle_back(self):
        """Gère le bouton 'Retour' (quitte le jeu)."""
        logger.info("User chose to exit from content warning")
        pygame.quit()
        exit()
    
    def update(self, dt):
        """Met à jour la scène."""
        pass  # Pas de logique de mise à jour nécessaire
    
    def draw(self, screen):
        """Dessine la scène."""
        # Fond noir
        screen.fill((0, 0, 0))
        
        # Panneau principal
        panel_width = WIDTH - 200
        panel_height = HEIGHT - 200
        panel_rect = pygame.Rect(
            (WIDTH - panel_width) // 2,
            (HEIGHT - panel_height) // 2,
            panel_width,
            panel_height
        )
        
        # Fond du panneau
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill(UI_PANEL)
        screen.blit(panel_surface, panel_rect.topleft)
        
        # Bordure du panneau
        pygame.draw.rect(screen, UI_TEXT, panel_rect, 3)
        
        # Titre
        if self.font_title:
            title_y = panel_rect.y + 40
            draw_text_centered(screen, "Avertissement de contenu", self.font_title, UI_TEXT, 
                             (WIDTH // 2, title_y))
        
        # Corps du texte
        if self.font_body:
            text_start_y = panel_rect.y + 100
            line_height = self.font_body.get_height() + 5
            
            for i, line in enumerate(self.warning_lines):
                if line.strip():  # Ligne non vide
                    y_pos = text_start_y + i * line_height
                    draw_text_centered(screen, line, self.font_body, UI_TEXT, 
                                     (WIDTH // 2, y_pos))
        
        # Boutons
        self._draw_button(screen, self.button_understand, "J'ai compris", "understand")
        self._draw_button(screen, self.button_back, "Retour", "back")
        
        # Instructions en bas
        if self.font_body:
            instruction_text = "Entrée: Continuer  •  Échap: Quitter"
            instruction_y = HEIGHT - 20
            draw_text_centered(screen, instruction_text, self.font_body, (150, 150, 150), 
                             (WIDTH // 2, instruction_y))
    
    def _draw_button(self, screen, button_rect, text, button_id):
        """
        Dessine un bouton.
        
        Args:
            screen: Surface de destination
            button_rect: Rectangle du bouton
            text: Texte du bouton
            button_id: ID du bouton pour le hover
        """
        # Couleur selon l'état
        if self.hovered_button == button_id:
            color = UI_HOVER
            border_width = 3
        else:
            color = UI_PANEL
            border_width = 2
        
        # Fond du bouton
        button_surface = pygame.Surface((button_rect.width, button_rect.height), pygame.SRCALPHA)
        button_surface.fill(color)
        screen.blit(button_surface, button_rect.topleft)
        
        # Bordure
        pygame.draw.rect(screen, UI_TEXT, button_rect, border_width)
        
        # Texte
        if self.font_button:
            draw_text_centered(screen, text, self.font_button, UI_TEXT, button_rect.center)
