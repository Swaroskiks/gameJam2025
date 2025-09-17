"""
Scène de pause pour A Day at the Office.
Menu pause avec options de reprise et retour au menu.
"""

import logging
import pygame
from src.core.scene_manager import Scene
from src.core.assets import asset_manager
from src.settings import WIDTH, HEIGHT, UI_PANEL, UI_TEXT, UI_HOVER
from src.core.utils import draw_text_centered

logger = logging.getLogger(__name__)


class PauseScene(Scene):
    """
    Scène de pause.
    
    Affichée par-dessus le gameplay quand le joueur appuie sur Échap.
    """
    
    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        
        # Polices
        self.font_title = None
        self.font_button = None
        
        # Boutons
        self.button_resume = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 60, 200, 50)
        self.button_menu = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 50)
        self.button_quit = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 60, 200, 50)
        
        # État
        self.hovered_button = None
        
        logger.info("PauseScene initialized")
    
    def enter(self, **kwargs):
        """Appelé en entrant dans la scène."""
        super().enter(**kwargs)
        
        # Charger les polices
        try:
            self.font_title = asset_manager.get_font("title_font")
            self.font_button = asset_manager.get_font("ui_font")
        except Exception as e:
            logger.error(f"Error loading fonts: {e}")
            # Fallback vers polices système
            self.font_title = pygame.font.SysFont(None, 48)
            self.font_button = pygame.font.SysFont(None, 24)
        
        logger.debug("Entered PauseScene")
    
    def handle_event(self, event):
        """Gère les événements."""
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            
            # Vérifier quel bouton est survolé
            if self.button_resume.collidepoint(mouse_pos):
                self.hovered_button = "resume"
            elif self.button_menu.collidepoint(mouse_pos):
                self.hovered_button = "menu"
            elif self.button_quit.collidepoint(mouse_pos):
                self.hovered_button = "quit"
            else:
                self.hovered_button = None
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche
                if self.button_resume.collidepoint(event.pos):
                    self._handle_resume()
                elif self.button_menu.collidepoint(event.pos):
                    self._handle_menu()
                elif self.button_quit.collidepoint(event.pos):
                    self._handle_quit()
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                self._handle_resume()
            elif event.key == pygame.K_RETURN:
                self._handle_resume()
            elif event.key == pygame.K_m:
                self._handle_menu()
            elif event.key == pygame.K_q:
                self._handle_quit()
    
    def _handle_resume(self):
        """Reprend le jeu."""
        logger.info("Resuming game")
        # Retourner à la scène précédente
        self.scene_manager.pop_scene()
    
    def _handle_menu(self):
        """Retourne au menu principal."""
        logger.info("Returning to main menu")
        # Vider la pile et aller au menu
        self.scene_manager.clear_stack()
        self.scene_manager.switch_scene("menu")
    
    def _handle_quit(self):
        """Quitte le jeu."""
        logger.info("Quitting game from pause")
        pygame.quit()
        exit()
    
    def update(self, dt):
        """Met à jour la scène."""
        pass  # Pas de logique de mise à jour nécessaire
    
    def draw(self, screen):
        """Dessine la scène."""
        # Arrière-plan wtc.png
        try:
            wtc_bg = pygame.image.load("assets/images/wtc.png").convert()
            wtc_bg = pygame.transform.scale(wtc_bg, (WIDTH, HEIGHT))
            screen.blit(wtc_bg, (0, 0))
        except:
            # Fallback vers fond noir
            screen.fill((0, 0, 0))
        
        # Overlay semi-transparent
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Noir semi-transparent
        screen.blit(overlay, (0, 0))
        
        # Panneau principal
        panel_width = 400
        panel_height = 300
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
            draw_text_centered(screen, "Pause", self.font_title, UI_TEXT, 
                             (WIDTH // 2, title_y))
        
        # Boutons
        self._draw_button(screen, self.button_resume, "Reprendre", "resume")
        self._draw_button(screen, self.button_menu, "Menu Principal", "menu")
        self._draw_button(screen, self.button_quit, "Quitter", "quit")
        
        # Instructions en bas
        if self.font_button:
            instructions = [
                "Échap/P: Reprendre",
                "M: Menu  •  Q: Quitter"
            ]
            
            y_start = panel_rect.bottom + 20
            for i, instruction in enumerate(instructions):
                y_pos = y_start + i * 25
                draw_text_centered(screen, instruction, self.font_button, (150, 150, 150), 
                                 (WIDTH // 2, y_pos))
    
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
