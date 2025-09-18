"""
Système de sons d'ambiance aléatoires pour créer une atmosphère de bureau réaliste.
"""
import random
import logging
from typing import Optional
from src.core.audio_manager import AudioManager

logger = logging.getLogger(__name__)

class AmbientSoundManager:
    """Gestionnaire des sons d'ambiance aléatoires."""
    
    def __init__(self, audio_manager: AudioManager):
        self.audio_manager = audio_manager
        self.phone_timer = 0.0
        self.keyboard_timer = 0.0
        self.coffee_timer = 0.0
        
        # Intervalles de temps pour les sons (en secondes)
        self.phone_interval = (15.0, 45.0)  # Téléphone toutes les 15-45 secondes
        self.keyboard_interval = (8.0, 25.0)  # Clavier toutes les 8-25 secondes
        self.coffee_interval = (20.0, 60.0)  # Café toutes les 20-60 secondes
        
        # Probabilité d'occurrence (0.0 à 1.0)
        self.phone_probability = 0.8  # 80% de chance
        self.keyboard_probability = 0.9  # 90% de chance
        self.coffee_probability = 0.5  # 50% de chance
        
        logger.info("AmbientSoundManager initialized")
    
    def update(self, dt: float):
        """
        Met à jour les timers et joue les sons d'ambiance.
        
        Args:
            dt: Temps écoulé depuis la dernière frame (en secondes)
        """
        # Mettre à jour les timers
        self.phone_timer -= dt
        self.keyboard_timer -= dt
        self.coffee_timer -= dt
        
        # Vérifier et jouer les sons
        self._check_phone_sound()
        self._check_keyboard_sound()
        self._check_coffee_sound()
    
    def _check_phone_sound(self):
        """Vérifie et joue le son de téléphone si nécessaire."""
        if self.phone_timer <= 0:
            if random.random() < self.phone_probability:
                self.audio_manager.play_sound("phone_pickup")
                logger.debug("Playing ambient phone sound")
            
            # Programmer le prochain son
            self.phone_timer = random.uniform(*self.phone_interval)
    
    def _check_keyboard_sound(self):
        """Vérifie et joue le son de clavier si nécessaire."""
        if self.keyboard_timer <= 0:
            if random.random() < self.keyboard_probability:
                self.audio_manager.play_sound("keyboard_typing")
                logger.debug("Playing ambient keyboard sound")
            
            # Programmer le prochain son
            self.keyboard_timer = random.uniform(*self.keyboard_interval)
    
    def _check_coffee_sound(self):
        """Vérifie et joue le son de café si nécessaire."""
        if self.coffee_timer <= 0:
            if random.random() < self.coffee_probability:
                self.audio_manager.play_sound("coffee_sip")
                logger.debug("Playing ambient coffee sound")
            
            # Programmer le prochain son
            self.coffee_timer = random.uniform(*self.coffee_interval)
    
    def set_phone_interval(self, min_seconds: float, max_seconds: float):
        """Définit l'intervalle pour les sons de téléphone."""
        self.phone_interval = (min_seconds, max_seconds)
    
    def set_keyboard_interval(self, min_seconds: float, max_seconds: float):
        """Définit l'intervalle pour les sons de clavier."""
        self.keyboard_interval = (min_seconds, max_seconds)
    
    def set_coffee_interval(self, min_seconds: float, max_seconds: float):
        """Définit l'intervalle pour les sons de café."""
        self.coffee_interval = (min_seconds, max_seconds)
    
    def set_phone_probability(self, probability: float):
        """Définit la probabilité d'occurrence des sons de téléphone (0.0 à 1.0)."""
        self.phone_probability = max(0.0, min(1.0, probability))
    
    def set_keyboard_probability(self, probability: float):
        """Définit la probabilité d'occurrence des sons de clavier (0.0 à 1.0)."""
        self.keyboard_probability = max(0.0, min(1.0, probability))
    
    def set_coffee_probability(self, probability: float):
        """Définit la probabilité d'occurrence des sons de café (0.0 à 1.0)."""
        self.coffee_probability = max(0.0, min(1.0, probability))
    
    def force_phone_sound(self):
        """Force le jeu d'un son de téléphone immédiatement."""
        self.audio_manager.play_sound("phone_pickup")
        self.phone_timer = random.uniform(*self.phone_interval)
    
    def force_keyboard_sound(self):
        """Force le jeu d'un son de clavier immédiatement."""
        self.audio_manager.play_sound("keyboard_typing")
        self.keyboard_timer = random.uniform(*self.keyboard_interval)
    
    def force_coffee_sound(self):
        """Force le jeu d'un son de café immédiatement."""
        self.audio_manager.play_sound("coffee_sip")
        self.coffee_timer = random.uniform(*self.coffee_interval)
    
    def reset_timers(self):
        """Remet à zéro tous les timers."""
        self.phone_timer = random.uniform(*self.phone_interval)
        self.keyboard_timer = random.uniform(*self.keyboard_interval)
        self.coffee_timer = random.uniform(*self.coffee_interval)
        logger.debug("Ambient sound timers reset")
