"""
Gestionnaire audio pour les effets sonores et la musique.
"""
import pygame
import logging
from typing import Dict, Optional
from src.core.assets import AssetManager

logger = logging.getLogger(__name__)

class AudioManager:
    """Gestionnaire des effets sonores et de la musique."""
    
    def __init__(self, asset_manager: AssetManager):
        self.asset_manager = asset_manager
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.music_playing = None
        self.master_volume = 0.7
        self.sfx_volume = 0.5
        self.music_volume = 0.3
        
        # Initialiser pygame.mixer si pas déjà fait
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Charger les sons
        self._load_sounds()
    
    def _load_sounds(self):
        """Charge tous les sons depuis le manifest."""
        try:
            # Charger les SFX
            sfx_assets = self.asset_manager.get_manifest_section("sfx")
            if sfx_assets:
                for sound_id, sound_data in sfx_assets.items():
                    try:
                        sound_path = sound_data.get("path")
                        if sound_path:
                            full_path = f"assets/{sound_path}"
                            sound = pygame.mixer.Sound(full_path)
                            # Appliquer le volume spécifique si défini
                            volume = sound_data.get("volume", 1.0)
                            sound.set_volume(volume * self.sfx_volume)
                            self.sounds[sound_id] = sound
                            logger.debug(f"Loaded sound: {sound_id}")
                    except Exception as e:
                        logger.warning(f"Failed to load sound {sound_id}: {e}")
            
            logger.info(f"Loaded {len(self.sounds)} sounds")
        except Exception as e:
            logger.error(f"Error loading sounds: {e}")
    
    def play_sound(self, sound_id: str, volume: Optional[float] = None) -> bool:
        """
        Joue un effet sonore.
        
        Args:
            sound_id: ID du son dans le manifest
            volume: Volume spécifique (optionnel)
            
        Returns:
            True si le son a été joué avec succès
        """
        try:
            if sound_id in self.sounds:
                sound = self.sounds[sound_id]
                if volume is not None:
                    original_volume = sound.get_volume()
                    sound.set_volume(volume * self.sfx_volume)
                    sound.play()
                    sound.set_volume(original_volume)
                else:
                    sound.play()
                return True
            else:
                logger.warning(f"Sound not found: {sound_id}")
                return False
        except Exception as e:
            logger.error(f"Error playing sound {sound_id}: {e}")
            return False
    
    def play_music(self, music_id: str, loop: int = -1) -> bool:
        """
        Joue une musique de fond.
        
        Args:
            music_id: ID de la musique dans le manifest
            loop: Nombre de boucles (-1 pour infini)
            
        Returns:
            True si la musique a été jouée avec succès
        """
        try:
            music_assets = self.asset_manager.get_manifest_section("music")
            if music_id in music_assets:
                music_path = music_assets[music_id]["path"]
                full_path = f"assets/{music_path}"
                pygame.mixer.music.load(full_path)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(loop)
                self.music_playing = music_id
                logger.info(f"Playing music: {music_id}")
                return True
            else:
                logger.warning(f"Music not found: {music_id}")
                return False
        except Exception as e:
            logger.error(f"Error playing music {music_id}: {e}")
            return False
    
    def stop_music(self):
        """Arrête la musique de fond."""
        pygame.mixer.music.stop()
        self.music_playing = None
    
    def set_master_volume(self, volume: float):
        """Définit le volume principal (0.0 à 1.0)."""
        self.master_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
        for sound in self.sounds.values():
            sound.set_volume(sound.get_volume() * self.master_volume)
    
    def set_sfx_volume(self, volume: float):
        """Définit le volume des effets sonores (0.0 à 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(sound.get_volume() * self.sfx_volume)
    
    def set_music_volume(self, volume: float):
        """Définit le volume de la musique (0.0 à 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        if self.music_playing:
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
    
    def get_available_sounds(self) -> list:
        """Retourne la liste des sons disponibles."""
        return list(self.sounds.keys())
    
    def is_sound_playing(self, sound_id: str) -> bool:
        """Vérifie si un son est en cours de lecture."""
        if sound_id in self.sounds:
            return pygame.mixer.get_busy()
        return False
