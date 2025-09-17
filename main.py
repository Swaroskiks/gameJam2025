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

# Imports du système principal
from src.settings import WIDTH, HEIGHT, FPS, GAME_TITLE


def main():
    """Point d'entrée principal du jeu."""
    logger.info("Starting A Day at the Office")
    
    # Utiliser le nouveau système uniquement
    if NEW_SYSTEM_AVAILABLE:
        logger.info("Using new game system")
        game = Game()
        game.run()
    else:
        logger.error("New system not available")
        sys.exit(1)




if __name__ == "__main__":
    main()