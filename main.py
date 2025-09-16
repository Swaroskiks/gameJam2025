"""
Point d'entrée principal pour A Day at the Office.
Intègre le nouveau système avec fallback vers l'ancien code.
"""

import pygame
import sys
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Imports du nouveau système
try:
    from src.core.app import Game
    NEW_SYSTEM_AVAILABLE = True
    logger.info("New system available")
except ImportError as e:
    logger.error(f"Could not import new system: {e}")
    NEW_SYSTEM_AVAILABLE = False

# Imports de l'ancien système (fallback)
from src.settings import WIDTH, HEIGHT, FPS, GAME_TITLE
from src.menu import menu_loop
from src.credits import credits_loop


def main():
    """Point d'entrée principal du jeu."""
    logger.info("Starting A Day at the Office")
    
    # Essayer le nouveau système d'abord
    if NEW_SYSTEM_AVAILABLE:
        try:
            logger.info("Using new game system")
            game = Game()
            game.run()
            return
        except Exception as e:
            logger.error(f"New system failed: {e}")
            logger.info("Falling back to old system")
    
    # Fallback vers l'ancien système
    logger.info("Using fallback system")
    run_fallback_system()


def run_fallback_system():
    """
    Lance l'ancien système en cas de problème avec le nouveau.
    """
    pygame.init()
    pygame.display.set_caption(GAME_TITLE)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    logger.info("Fallback system initialized")

    try:
        while True:
            choice = menu_loop(screen, clock)

            if choice == "jouer":
                # Utiliser l'ancien game_loop si disponible
                try:
                    from src.game_backup import game_loop
                    game_loop(screen, clock)
                except ImportError:
                    logger.error("No game loop available")
                    # Afficher un message d'erreur simple
                    show_error_message(screen, clock, "Gameplay non disponible")
                    
            elif choice in ("crédits", "credits"):
                credits_loop(screen, clock)
                
            elif choice in ("options",):
                show_error_message(screen, clock, "Options non implémentées")
                
            elif choice in ("quit", "quitter"):
                break

            clock.tick(FPS)

    except Exception as e:
        logger.error(f"Error in fallback system: {e}")
    finally:
        pygame.quit()
        sys.exit()


def show_error_message(screen, clock, message):
    """
    Affiche un message d'erreur simple.
    
    Args:
        screen: Surface d'affichage
        clock: Horloge pygame
        message: Message à afficher
    """
    font = pygame.font.SysFont(None, 48)
    
    # Boucle d'affichage du message
    start_time = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_time < 3000:  # 3 secondes
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return
        
        screen.fill((50, 50, 50))
        
        # Texte d'erreur
        text_surface = font.render(message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text_surface, text_rect)
        
        # Instructions
        small_font = pygame.font.SysFont(None, 24)
        instruction = small_font.render("Appuyez sur une touche pour continuer", True, (200, 200, 200))
        instruction_rect = instruction.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(instruction, instruction_rect)
        
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()