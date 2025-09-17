"""
Scène de menu principal adaptée pour A Day at the Office.
Adaptation du menu existant au nouveau système de scènes.
"""

import logging
import pygame
import sys
from src.core.scene_manager import Scene
from src.core.assets import asset_manager
from src.settings import WIDTH, HEIGHT, FPS, WHITE, UI_HOVER, UI_PANEL

logger = logging.getLogger(__name__)


class MenuScene(Scene):
    """
    Scène de menu principal.
    
    Adaptation du menu existant pour s'intégrer au nouveau système de scènes.
    """
    
    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        
        # Font
        self.font = None
        
        # Boutons (adaptés du code existant)
        self.button_texts = ["Jouer", "Options", "Crédits", "Quitter"]
        self.buttons = []
        self.button_width, self.button_height = 300, 80
        self.spacing = 20
        
        # Arrière-plan
        self.background = None
        
        logger.info("MenuScene initialized")
    
    def enter(self, **kwargs):
        """Appelé en entrant dans la scène."""
        super().enter(**kwargs)
        
        # Charger la police
        try:
            self.font = asset_manager.get_font("title_font")  # Utilise la police du manifest
        except Exception as e:
            logger.error(f"Error loading menu font: {e}")
            # Fallback vers la police existante
            try:
                self.font = pygame.font.Font("assets/fonts/Pixellari.ttf", 60)
            except:
                self.font = pygame.font.SysFont(None, 60)
        
        # Charger l'arrière-plan wtc.png directement
        try:
            self.background = pygame.image.load("assets/images/wtc.png").convert()
            self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
        except Exception as e:
            logger.error(f"Error loading wtc.png: {e}")
            # Créer un fond de couleur simple
            self.background = pygame.Surface((WIDTH, HEIGHT))
            self.background.fill((50, 50, 100))
        
        # Créer les rectangles des boutons (code existant adapté)
        self._setup_buttons()
        
        logger.debug("Entered MenuScene")
    
    def _setup_buttons(self):
        """Configure les boutons du menu."""
        self.buttons.clear()
        
        total_height = len(self.button_texts) * self.button_height + (len(self.button_texts)-1) * self.spacing
        start_y = (HEIGHT - total_height) // 2
        
        for i, text in enumerate(self.button_texts):
            rect = pygame.Rect(
                (WIDTH - self.button_width) // 2,
                start_y + i * (self.button_height + self.spacing),
                self.button_width,
                self.button_height
            )
            self.buttons.append((rect, text))
    
    def handle_event(self, event):
        """Gère les événements."""
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, text in self.buttons:
                if rect.collidepoint(event.pos):
                    self._handle_button_click(text)
        
        elif event.type == pygame.KEYDOWN:
            # Raccourcis clavier
            if event.key == pygame.K_RETURN:
                self._handle_button_click("Jouer")
            elif event.key == pygame.K_ESCAPE:
                self._handle_button_click("Quitter")
    
    def _handle_button_click(self, button_text):
        """
        Gère le clic sur un bouton.
        
        Args:
            button_text: Texte du bouton cliqué
        """
        text_lower = button_text.lower()
        
        if text_lower == "jouer":
            logger.info("Starting gameplay")
            self.switch_to("gameplay")
        
        elif text_lower == "options":
            logger.info("Options not implemented yet")
            # TODO: Implémenter les options
            pass
        
        elif text_lower == "crédits":
            logger.info("Showing credits")
            # Utiliser l'écran de crédits existant (pour l'instant)
            from src.credits import credits_loop
            credits_loop(pygame.display.get_surface(), pygame.time.Clock())
        
        elif text_lower == "quitter":
            logger.info("Quitting game")
            self.scene_manager.quit_game()
    
    def update(self, dt):
        """Met à jour la scène."""
        pass  # Pas de logique de mise à jour nécessaire pour le menu
    
    def draw(self, screen):
        """Dessine la scène."""
        # Arrière-plan
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((50, 50, 100))
        
        # Boutons (code existant adapté)
        mouse_pos = pygame.mouse.get_pos()
        
        for rect, text in self.buttons:
            # Surface du bouton avec transparence
            button_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            
            if rect.collidepoint(mouse_pos):
                button_surface.fill(UI_HOVER)  # Utilise les couleurs du nouveau système
            else:
                button_surface.fill(UI_PANEL)
            
            screen.blit(button_surface, rect.topleft)
            
            # Texte du bouton
            if self.font:
                text_surface = self.font.render(text, True, WHITE)
                text_rect = text_surface.get_rect(center=rect.center)
                screen.blit(text_surface, text_rect)
    
    def exit(self):
        """Appelé en quittant la scène."""
        super().exit()
        logger.debug("Exited MenuScene")
