"""
Classe principale de l'application A Day at the Office.
Gère l'initialisation, la boucle principale, et l'intégration des systèmes.
"""

import sys
import logging
from typing import Optional
import pygame

from src.settings import (
    WINDOW_SIZE, FPS, GAME_TITLE, DEV_MODE,
    START_TIME, END_TIME, GAME_SECONDS_PER_REAL_SECOND
)
from src.core.scene_manager import SceneManager
from src.core.timer import GameClock
from src.core.assets import asset_manager
from src.core.input import InputManager

logger = logging.getLogger(__name__)


class Game:
    """
    Classe principale du jeu A Day at the Office.
    
    Gère l'initialisation de pygame, la boucle principale,
    et coordonne tous les systèmes (scènes, assets, timer, etc.).
    """
    
    def __init__(self):
        self.running = False
        self.clock = pygame.time.Clock()
        self.screen: Optional[pygame.Surface] = None
        
        # Systèmes principaux
        self.scene_manager = SceneManager()
        self.game_clock = GameClock(START_TIME, END_TIME, GAME_SECONDS_PER_REAL_SECOND)
        self.input_manager = InputManager()
        
        # État du jeu
        self.paused = False
        
        logger.info("Game instance created")
    
    def initialize(self) -> bool:
        """
        Initialise pygame et tous les systèmes.
        
        Returns:
            True si l'initialisation a réussi
        """
        try:
            # Initialiser pygame
            pygame.init()
            
            # Créer la fenêtre
            self.screen = pygame.display.set_mode(WINDOW_SIZE)
            pygame.display.set_caption(GAME_TITLE)
            
            # Charger les assets
            if not asset_manager.load_manifest():
                logger.warning("Could not load asset manifest, using placeholders")
            
            # Enregistrer les scènes
            self._register_scenes()
            
            # Démarrer directement avec le menu (avertissement supprimé)
            if not self.scene_manager.switch_scene("menu"):
                logger.error("Could not start with menu scene")
                return False
            
            logger.info("Game initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize game: {e}")
            return False
    
    def _register_scenes(self) -> None:
        """Enregistre toutes les scènes du jeu."""
        try:
            # Import des scènes (import tardif pour éviter les dépendances circulaires)
            from src.scenes.content_warning import ContentWarningScene
            from src.scenes.menu import MenuScene
            from src.scenes.gameplay import GameplayScene
            from src.scenes.pause import PauseScene
            from src.scenes.summary import SummaryScene
            
            # Enregistrement
            self.scene_manager.register_scene("content_warning", ContentWarningScene)
            self.scene_manager.register_scene("menu", MenuScene)
            self.scene_manager.register_scene("gameplay", GameplayScene)
            self.scene_manager.register_scene("pause", PauseScene)
            self.scene_manager.register_scene("summary", SummaryScene)
            
            logger.info("All scenes registered")
            
        except ImportError as e:
            logger.error(f"Could not import scene: {e}")
            # Fallback: enregistrer au moins les scènes de base
            self._register_fallback_scenes()
    
    def _register_fallback_scenes(self) -> None:
        """Enregistre des scènes de fallback en cas d'erreur d'import."""
        from src.scenes.fallback import FallbackMenuScene, FallbackGameScene
        
        self.scene_manager.register_scene("content_warning", FallbackMenuScene)
        self.scene_manager.register_scene("menu", FallbackMenuScene)
        self.scene_manager.register_scene("gameplay", FallbackGameScene)
        
        logger.warning("Using fallback scenes")
    
    def run(self) -> None:
        """Lance la boucle principale du jeu."""
        if not self.initialize():
            logger.error("Failed to initialize, exiting")
            return
        
        self.running = True
        logger.info("Starting main game loop")
        
        try:
            while self.running:
                dt = self.clock.tick(FPS) / 1000.0  # Delta time en secondes
                
                # Gestion des événements
                self._handle_events()
                
                # Mise à jour
                if not self.paused:
                    self._update(dt)
                
                # Rendu
                self._draw()
                
                # Affichage
                pygame.display.flip()
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self._cleanup()
    
    def _handle_events(self) -> None:
        """Gère tous les événements pygame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
                return
            
            # Raccourcis globaux
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5 and DEV_MODE:
                    # Hot-reload des assets
                    asset_manager.reload_manifest()
                    logger.info("Assets reloaded")
                elif event.key == pygame.K_ESCAPE:
                    # Gestion de la pause
                    self._handle_escape()
            
            # Transmettre à l'input manager
            self.input_manager.handle_event(event)
            
            # Transmettre à la scène actuelle
            self.scene_manager.handle_event(event)
    
    def _handle_escape(self) -> None:
        """Gère la touche Échap selon le contexte."""
        current_scene = self.scene_manager.get_current_scene_name()
        
        if current_scene == "gameplay" and not self.paused:
            # Ouvrir le menu pause
            self.scene_manager.push_scene("pause")
            self.paused = True
        elif current_scene == "pause":
            # Fermer le menu pause
            self.scene_manager.pop_scene()
            self.paused = False
        elif current_scene in ["menu", "content_warning"]:
            # Quitter le jeu
            self.quit()
    
    def _update(self, dt: float) -> None:
        """Met à jour tous les systèmes."""
        # Mettre à jour l'horloge de jeu
        self.game_clock.tick(dt)
        
        # Mettre à jour l'input manager
        self.input_manager.update()
        
        # Mettre à jour la scène actuelle
        self.scene_manager.update(dt)
        
        # Vérifier si la deadline est atteinte
        if self.game_clock.is_deadline():
            current_scene = self.scene_manager.get_current_scene_name()
            if current_scene == "gameplay":
                # Passer automatiquement au résumé
                self.scene_manager.switch_scene("summary")
    
    def _draw(self) -> None:
        """Dessine tout à l'écran."""
        if not self.screen:
            return
        
        # Effacer l'écran
        self.screen.fill((0, 0, 0))
        
        # Dessiner la scène actuelle
        self.scene_manager.draw(self.screen)
        
        # Debug supprimé - logs console uniquement
    
    
    def _cleanup(self) -> None:
        """Nettoie les ressources avant la fermeture."""
        logger.info("Cleaning up...")
        
        # Arrêter la musique
        pygame.mixer.stop()
        
        # Quitter pygame
        pygame.quit()
        
        logger.info("Cleanup complete")
    
    def quit(self) -> None:
        """Déclenche la fermeture du jeu."""
        self.running = False
        logger.info("Game quit requested")
    
    def switch_scene(self, scene_name: str, **kwargs) -> bool:
        """
        Raccourci pour changer de scène.
        
        Args:
            scene_name: Nom de la scène de destination
            **kwargs: Données à passer à la nouvelle scène
            
        Returns:
            True si le changement a réussi
        """
        return self.scene_manager.switch_scene(scene_name, **kwargs)
    
    def get_game_clock(self) -> GameClock:
        """Retourne l'horloge de jeu."""
        return self.game_clock
    
    def get_input_manager(self) -> InputManager:
        """Retourne le gestionnaire d'entrées."""
        return self.input_manager
    
    def get_scene_manager(self) -> SceneManager:
        """Retourne le gestionnaire de scènes."""
        return self.scene_manager
