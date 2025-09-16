"""
Scènes de fallback en cas d'erreur d'import.
Versions simplifiées pour assurer que le jeu démarre.
"""

import pygame
from src.core.scene_manager import Scene
from src.settings import WIDTH, HEIGHT, WHITE, BLACK


class FallbackMenuScene(Scene):
    """Menu de fallback simple."""
    
    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        self.font = None
    
    def enter(self, **kwargs):
        super().enter(**kwargs)
        try:
            self.font = pygame.font.SysFont(None, 48)
        except:
            self.font = pygame.font.Font(None, 48)
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.switch_to("gameplay")
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                exit()
    
    def update(self, dt):
        pass
    
    def draw(self, screen):
        screen.fill(BLACK)
        
        if self.font:
            title = self.font.render("A Day at the Office", True, WHITE)
            title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
            screen.blit(title, title_rect)
            
            instruction = self.font.render("Press SPACE to start", True, WHITE)
            inst_rect = instruction.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
            screen.blit(instruction, inst_rect)


class FallbackGameScene(Scene):
    """Scène de jeu de fallback."""
    
    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        self.font = None
    
    def enter(self, **kwargs):
        super().enter(**kwargs)
        try:
            self.font = pygame.font.SysFont(None, 36)
        except:
            self.font = pygame.font.Font(None, 36)
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_to("menu")
    
    def update(self, dt):
        pass
    
    def draw(self, screen):
        screen.fill(BLACK)
        
        if self.font:
            message = self.font.render("Fallback Game Scene", True, WHITE)
            msg_rect = message.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(message, msg_rect)
            
            instruction = self.font.render("Press ESC to return to menu", True, WHITE)
            inst_rect = instruction.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
            screen.blit(instruction, inst_rect)
