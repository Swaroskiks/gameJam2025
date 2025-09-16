"""
Tests pour le système d'horloge diégétique.
"""

import pytest
from datetime import datetime, timedelta
from src.core.timer import GameClock


class TestGameClock:
    """Tests pour GameClock."""
    
    def test_initialization(self):
        """Test de l'initialisation de l'horloge."""
        clock = GameClock("08:30", "08:48", 5.0)
        
        assert clock.speed == 5.0
        assert clock.get_time_str() == "08:30"
        assert not clock.is_running
        assert not clock.is_deadline()
        assert clock.get_progress() == 0.0
    
    def test_start_stop(self):
        """Test du démarrage et arrêt."""
        clock = GameClock("08:30", "08:48")
        
        clock.start()
        assert clock.is_running
        
        clock.stop()
        assert not clock.is_running
    
    def test_tick_progression(self):
        """Test de la progression avec tick."""
        clock = GameClock("08:30", "08:48", 60.0)  # 1 minute réelle = 1 heure de jeu
        clock.start()
        
        # Simuler 1 seconde réelle (= 1 minute de jeu)
        clock.tick(1.0)
        
        assert clock.get_time_str() == "08:31"
        assert clock.get_progress() > 0.0
        assert not clock.is_deadline()
    
    def test_deadline_reached(self):
        """Test de l'atteinte de la deadline."""
        clock = GameClock("08:30", "08:48", 1000.0)  # Très rapide
        clock.start()
        
        # Simuler assez de temps pour atteindre la deadline
        clock.tick(100.0)
        
        assert clock.is_deadline()
        assert clock.get_progress() == 1.0
        assert not clock.is_running  # Doit s'arrêter automatiquement
    
    def test_reset(self):
        """Test de la remise à zéro."""
        clock = GameClock("08:30", "08:48", 60.0)
        clock.start()
        clock.tick(5.0)
        
        # Vérifier qu'on a avancé
        assert clock.get_time_str() != "08:30"
        
        clock.reset()
        
        assert clock.get_time_str() == "08:30"
        assert clock.get_progress() == 0.0
        assert clock.total_real_seconds == 0.0
    
    def test_time_comparisons(self):
        """Test des comparaisons temporelles."""
        clock = GameClock("08:30", "08:48", 60.0)
        clock.start()
        clock.tick(2.0)  # Avancer de 2 minutes de jeu
        
        assert clock.is_time_after("08:30")
        assert clock.is_time_before("08:48")
        assert not clock.is_time_before("08:30")
        assert not clock.is_time_after("08:48")
    
    def test_remaining_time(self):
        """Test du calcul du temps restant."""
        clock = GameClock("08:30", "08:48", 60.0)  # 18 minutes de jeu
        clock.start()
        clock.tick(5.0)  # 5 minutes de jeu écoulées
        
        remaining = clock.get_remaining_time()
        remaining_minutes = clock.get_remaining_minutes()
        
        assert remaining_minutes == 13  # 18 - 5 = 13
        assert remaining.total_seconds() > 0
    
    def test_invalid_time_format(self):
        """Test avec format d'heure invalide."""
        with pytest.raises(ValueError):
            GameClock("25:00", "08:48")
        
        with pytest.raises(ValueError):
            GameClock("08:30", "invalid")
    
    def test_format_time(self):
        """Test du formatage des heures."""
        clock = GameClock("08:30", "08:48")
        
        # Test avec heure actuelle
        formatted = clock.format_time()
        assert formatted == "08:30"
        
        # Test avec heure spécifique
        test_time = datetime(2001, 9, 11, 10, 15, 30)
        formatted = clock.format_time(test_time)
        assert formatted == "10:15"
    
    def test_speed_effects(self):
        """Test des effets de la vitesse."""
        # Horloge lente
        slow_clock = GameClock("08:30", "08:48", 1.0)
        slow_clock.start()
        slow_clock.tick(1.0)
        slow_time = slow_clock.get_time()
        
        # Horloge rapide
        fast_clock = GameClock("08:30", "08:48", 10.0)
        fast_clock.start()
        fast_clock.tick(1.0)
        fast_time = fast_clock.get_time()
        
        # L'horloge rapide doit avoir plus avancé
        assert fast_time > slow_time
    
    def test_pause_resume(self):
        """Test de la pause et reprise."""
        clock = GameClock("08:30", "08:48", 60.0)
        clock.start()
        
        # Avancer un peu
        clock.tick(1.0)
        time_before_pause = clock.get_time()
        
        # Mettre en pause
        clock.stop()
        
        # Essayer d'avancer (ne devrait pas bouger)
        clock.tick(1.0)
        assert clock.get_time() == time_before_pause
        
        # Reprendre
        clock.start()
        clock.tick(1.0)
        assert clock.get_time() > time_before_pause
