"""
Système d'animation pour A Day at the Office.
Gère les spritesheets et animations temporelles.
"""

import logging
from typing import Dict, Any, Optional, List
import pygame
from src.core.assets import asset_manager

logger = logging.getLogger(__name__)


class Animation:
    """
    Représente une animation basée sur une spritesheet.
    """
    
    def __init__(self, spritesheet_key: str, loop: bool = True, auto_start: bool = True):
        """
        Initialise une animation.
        
        Args:
            spritesheet_key: Clé de la spritesheet dans le manifest
            loop: Si l'animation doit boucler
            auto_start: Si l'animation démarre automatiquement
        """
        self.spritesheet_key = spritesheet_key
        self.loop = loop
        self.is_playing = auto_start
        self.current_frame = 0
        self.time_accumulator = 0.0
        
        # Charger la spritesheet et ses métadonnées
        self.spritesheet, self.metadata = asset_manager.get_spritesheet(spritesheet_key)
        
        # Extraire les paramètres
        self.frame_width = self.metadata.get("frame_w", 32)
        self.frame_height = self.metadata.get("frame_h", 32)
        self.fps = self.metadata.get("fps", 8)
        self.frame_count = self.metadata.get("frames", 2)
        
        # Calculer le temps par frame
        self.frame_duration = 1.0 / self.fps if self.fps > 0 else 0.1
        
        # Extraire les frames
        self.frames = self._extract_frames()
        
        logger.debug(f"Animation created: {spritesheet_key} ({len(self.frames)} frames)")
    
    def _extract_frames(self) -> List[pygame.Surface]:
        """
        Extrait les frames individuelles de la spritesheet.
        
        Returns:
            Liste des surfaces des frames
        """
        frames = []
        
        # Calculer combien de frames on peut extraire
        sheet_width = self.spritesheet.get_width()
        sheet_height = self.spritesheet.get_height()
        
        frames_per_row = sheet_width // self.frame_width
        frames_per_col = sheet_height // self.frame_height
        max_frames = frames_per_row * frames_per_col
        
        # Limiter au nombre de frames spécifié
        actual_frame_count = min(self.frame_count, max_frames)
        
        for i in range(actual_frame_count):
            # Calculer la position de la frame
            row = i // frames_per_row
            col = i % frames_per_row
            
            x = col * self.frame_width
            y = row * self.frame_height
            
            # Extraire la frame
            frame_rect = pygame.Rect(x, y, self.frame_width, self.frame_height)
            frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
            frame.blit(self.spritesheet, (0, 0), frame_rect)
            
            frames.append(frame)
        
        return frames
    
    def update(self, dt: float) -> None:
        """
        Met à jour l'animation.
        
        Args:
            dt: Temps écoulé depuis la dernière frame (en secondes)
        """
        if not self.is_playing or len(self.frames) <= 1:
            return
        
        self.time_accumulator += dt
        
        # Avancer les frames si nécessaire
        while self.time_accumulator >= self.frame_duration:
            self.time_accumulator -= self.frame_duration
            self.current_frame += 1
            
            # Gérer la fin de l'animation
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.is_playing = False
                    break
    
    def get_current_frame(self) -> pygame.Surface:
        """
        Retourne la frame actuelle de l'animation.
        
        Returns:
            Surface de la frame actuelle
        """
        if not self.frames:
            # Fallback: créer une surface vide
            return pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
        
        frame_index = min(self.current_frame, len(self.frames) - 1)
        return self.frames[frame_index]
    
    def play(self) -> None:
        """Démarre ou reprend l'animation."""
        self.is_playing = True
    
    def pause(self) -> None:
        """Met en pause l'animation."""
        self.is_playing = False
    
    def stop(self) -> None:
        """Arrête l'animation et remet au début."""
        self.is_playing = False
        self.current_frame = 0
        self.time_accumulator = 0.0
    
    def reset(self) -> None:
        """Remet l'animation au début sans l'arrêter."""
        self.current_frame = 0
        self.time_accumulator = 0.0
    
    def set_frame(self, frame_index: int) -> None:
        """
        Définit la frame actuelle.
        
        Args:
            frame_index: Index de la frame (0 à frame_count-1)
        """
        self.current_frame = max(0, min(frame_index, len(self.frames) - 1))
    
    def is_finished(self) -> bool:
        """
        Vérifie si l'animation non-bouclée est terminée.
        
        Returns:
            True si l'animation est finie
        """
        return not self.loop and not self.is_playing and self.current_frame >= len(self.frames) - 1


class AnimationManager:
    """
    Gestionnaire d'animations pour une entité.
    Permet de gérer plusieurs animations et les transitions.
    """
    
    def __init__(self):
        self.animations: Dict[str, Animation] = {}
        self.current_animation: Optional[str] = None
        self.default_animation: Optional[str] = None
    
    def add_animation(self, name: str, spritesheet_key: str, loop: bool = True, auto_start: bool = False) -> None:
        """
        Ajoute une animation.
        
        Args:
            name: Nom unique de l'animation
            spritesheet_key: Clé de la spritesheet
            loop: Si l'animation doit boucler
            auto_start: Si l'animation démarre automatiquement
        """
        animation = Animation(spritesheet_key, loop, auto_start)
        self.animations[name] = animation
        
        # Définir comme animation par défaut si c'est la première
        if not self.default_animation:
            self.default_animation = name
        
        logger.debug(f"Animation added: {name}")
    
    def play_animation(self, name: str, force_restart: bool = False) -> bool:
        """
        Lance une animation.
        
        Args:
            name: Nom de l'animation
            force_restart: Si True, redémarre l'animation même si déjà active
            
        Returns:
            True si l'animation a été lancée
        """
        if name not in self.animations:
            logger.warning(f"Animation not found: {name}")
            return False
        
        # Ne pas changer si c'est déjà l'animation courante (sauf force_restart)
        if self.current_animation == name and not force_restart:
            return True
        
        # Arrêter l'animation précédente
        if self.current_animation and self.current_animation in self.animations:
            self.animations[self.current_animation].pause()
        
        # Démarrer la nouvelle animation
        self.current_animation = name
        animation = self.animations[name]
        
        if force_restart:
            animation.reset()
        
        animation.play()
        return True
    
    def stop_current_animation(self) -> None:
        """Arrête l'animation courante."""
        if self.current_animation and self.current_animation in self.animations:
            self.animations[self.current_animation].stop()
        self.current_animation = None
    
    def update(self, dt: float) -> None:
        """
        Met à jour l'animation courante.
        
        Args:
            dt: Temps écoulé depuis la dernière frame
        """
        if self.current_animation and self.current_animation in self.animations:
            animation = self.animations[self.current_animation]
            animation.update(dt)
            
            # Si l'animation non-bouclée est finie, revenir à l'animation par défaut
            if animation.is_finished() and self.default_animation and self.current_animation != self.default_animation:
                self.play_animation(self.default_animation)
    
    def get_current_frame(self) -> Optional[pygame.Surface]:
        """
        Retourne la frame actuelle de l'animation courante.
        
        Returns:
            Surface de la frame ou None
        """
        if self.current_animation and self.current_animation in self.animations:
            return self.animations[self.current_animation].get_current_frame()
        
        # Fallback vers animation par défaut
        if self.default_animation and self.default_animation in self.animations:
            return self.animations[self.default_animation].get_current_frame()
        
        return None
    
    def has_animation(self, name: str) -> bool:
        """
        Vérifie si une animation existe.
        
        Args:
            name: Nom de l'animation
            
        Returns:
            True si l'animation existe
        """
        return name in self.animations
    
    def get_current_animation_name(self) -> Optional[str]:
        """Retourne le nom de l'animation courante."""
        return self.current_animation
    
    def set_default_animation(self, name: str) -> bool:
        """
        Définit l'animation par défaut.
        
        Args:
            name: Nom de l'animation par défaut
            
        Returns:
            True si l'animation existe et a été définie
        """
        if name in self.animations:
            self.default_animation = name
            return True
        return False
