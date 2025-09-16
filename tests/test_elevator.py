"""
Tests pour le système d'ascenseur.
"""

import pytest
from src.world.elevator import Elevator, ElevatorState
from src.settings import MIN_FLOOR, MAX_FLOOR


class TestElevator:
    """Tests pour la classe Elevator."""
    
    def setup_method(self):
        """Setup pour chaque test."""
        self.elevator = Elevator(x=100)
    
    def test_initialization(self):
        """Test de l'initialisation."""
        assert self.elevator.x == 100
        assert self.elevator.current_floor == MIN_FLOOR
        assert self.elevator.target_floor == MIN_FLOOR
        assert self.elevator.state == ElevatorState.IDLE
        assert self.elevator.display_floor == float(MIN_FLOOR)
        assert len(self.elevator.call_queue) == 0
    
    def test_call_same_floor(self):
        """Test d'appel à l'étage actuel."""
        # L'ascenseur est déjà au MIN_FLOOR
        result = self.elevator.call(MIN_FLOOR)
        
        assert result is True
        assert self.elevator.state == ElevatorState.OPENING_DOORS
        assert len(self.elevator.call_queue) == 0
    
    def test_call_different_floor(self):
        """Test d'appel à un étage différent."""
        target_floor = MIN_FLOOR + 2
        result = self.elevator.call(target_floor)
        
        assert result is True
        assert target_floor in self.elevator.call_queue
        assert self.elevator.state == ElevatorState.MOVING_UP
        assert self.elevator.target_floor == target_floor
    
    def test_invalid_floor_call(self):
        """Test d'appel à un étage invalide."""
        result = self.elevator.call(MAX_FLOOR + 10)
        assert result is False
        
        result = self.elevator.call(MIN_FLOOR - 10)
        assert result is False
    
    def test_go_to(self):
        """Test de la fonction go_to."""
        target_floor = MAX_FLOOR
        result = self.elevator.go_to(target_floor)
        
        assert result is True
        assert self.elevator.target_floor == target_floor
        assert self.elevator.state == ElevatorState.MOVING_UP
        assert self.elevator.total_uses == 1
    
    def test_movement_up(self):
        """Test du mouvement vers le haut."""
        target_floor = MIN_FLOOR + 1
        self.elevator.go_to(target_floor)
        
        # Simuler le temps de trajet
        travel_time = self.elevator.floor_travel_time + 0.1
        self.elevator.update(travel_time)
        
        assert self.elevator.current_floor == target_floor
        assert self.elevator.state == ElevatorState.OPENING_DOORS
        assert target_floor in self.elevator.floors_visited
    
    def test_movement_down(self):
        """Test du mouvement vers le bas."""
        # Commencer à un étage élevé
        start_floor = MAX_FLOOR
        self.elevator.current_floor = start_floor
        self.elevator.display_floor = float(start_floor)
        
        target_floor = MIN_FLOOR
        self.elevator.go_to(target_floor)
        
        assert self.elevator.state == ElevatorState.MOVING_DOWN
        
        # Simuler le temps de trajet complet
        floors_to_travel = start_floor - target_floor
        travel_time = floors_to_travel * self.elevator.floor_travel_time + 0.1
        self.elevator.update(travel_time)
        
        assert self.elevator.current_floor == target_floor
    
    def test_door_animation(self):
        """Test de l'animation des portes."""
        # Déclencher l'ouverture des portes
        self.elevator.call(MIN_FLOOR)  # Même étage
        
        assert self.elevator.state == ElevatorState.OPENING_DOORS
        
        # Simuler l'animation d'ouverture
        self.elevator.update(self.elevator.door_animation_duration + 0.1)
        
        assert self.elevator.state == ElevatorState.DOORS_OPEN
        assert self.elevator.are_doors_open() is True
        assert self.elevator.can_enter() is True
    
    def test_door_closing(self):
        """Test de la fermeture des portes."""
        # Ouvrir les portes d'abord
        self.elevator.call(MIN_FLOOR)
        self.elevator.update(self.elevator.door_animation_duration + 0.1)
        
        # Forcer la fermeture
        result = self.elevator.force_close_doors()
        
        assert result is True
        assert self.elevator.state == ElevatorState.CLOSING_DOORS
        
        # Simuler la fermeture
        self.elevator.update(self.elevator.door_animation_duration + 0.1)
        
        assert self.elevator.state == ElevatorState.IDLE
        assert self.elevator.are_doors_open() is False
    
    def test_queue_processing(self):
        """Test du traitement de la file d'attente."""
        # Ajouter plusieurs appels
        floors = [MIN_FLOOR + 1, MIN_FLOOR + 3, MIN_FLOOR + 2]
        for floor in floors:
            self.elevator.call(floor)
        
        assert len(self.elevator.call_queue) == 3
        
        # Le premier appel doit être traité
        assert self.elevator.target_floor == floors[0]
        assert self.elevator.state == ElevatorState.MOVING_UP
    
    def test_is_at_floor(self):
        """Test de la vérification d'étage."""
        assert self.elevator.is_at_floor(MIN_FLOOR) is True
        assert self.elevator.is_at_floor(MAX_FLOOR) is False
        
        # Pendant le mouvement, ne doit pas être "at floor"
        self.elevator.go_to(MIN_FLOOR + 1)
        assert self.elevator.is_at_floor(MIN_FLOOR) is False
        assert self.elevator.is_at_floor(MIN_FLOOR + 1) is False
    
    def test_is_moving(self):
        """Test de la détection de mouvement."""
        assert self.elevator.is_moving() is False
        
        self.elevator.go_to(MIN_FLOOR + 1)
        assert self.elevator.is_moving() is True
        
        # Simuler l'arrivée
        self.elevator.update(self.elevator.floor_travel_time + 0.1)
        assert self.elevator.is_moving() is False
    
    def test_display_position_interpolation(self):
        """Test de l'interpolation de position d'affichage."""
        start_floor = MIN_FLOOR
        target_floor = MIN_FLOOR + 2
        
        self.elevator.go_to(target_floor)
        
        # Au début, position d'affichage = étage actuel
        assert self.elevator.get_display_position() == float(start_floor)
        
        # À mi-chemin, position interpolée
        half_time = self.elevator.floor_travel_time
        self.elevator.update(half_time)
        
        display_pos = self.elevator.get_display_position()
        assert start_floor < display_pos < target_floor
    
    def test_door_animation_progress(self):
        """Test du progrès de l'animation des portes."""
        self.elevator.call(MIN_FLOOR)
        
        # Au début de l'ouverture
        assert self.elevator.get_door_animation_progress() == 0.0
        
        # À mi-chemin
        self.elevator.update(self.elevator.door_animation_duration / 2)
        progress = self.elevator.get_door_animation_progress()
        assert 0.0 < progress < 1.0
        
        # Complètement ouvertes
        self.elevator.update(self.elevator.door_animation_duration / 2 + 0.1)
        assert self.elevator.get_door_animation_progress() == 1.0
    
    def test_clear_queue(self):
        """Test du vidage de la file d'attente."""
        # Ajouter des appels
        self.elevator.call(MIN_FLOOR + 1)
        self.elevator.call(MIN_FLOOR + 2)
        
        assert len(self.elevator.call_queue) > 0
        
        self.elevator.clear_queue()
        
        assert len(self.elevator.call_queue) == 0
    
    def test_get_stats(self):
        """Test des statistiques."""
        self.elevator.go_to(MIN_FLOOR + 1)
        self.elevator.call(MIN_FLOOR + 2)
        
        stats = self.elevator.get_stats()
        
        assert stats["total_uses"] == 1
        assert stats["current_floor"] == MIN_FLOOR
        assert stats["state"] == ElevatorState.MOVING_UP.value
        assert stats["queue_length"] == 1  # Un appel en attente
    
    def test_callback_system(self):
        """Test du système de callbacks."""
        floor_reached_called = False
        doors_opened_called = False
        
        def on_floor_reached(floor):
            nonlocal floor_reached_called
            floor_reached_called = True
        
        def on_doors_opened():
            nonlocal doors_opened_called
            doors_opened_called = True
        
        self.elevator.on_floor_reached = on_floor_reached
        self.elevator.on_doors_opened = on_doors_opened
        
        # Aller à un étage
        target_floor = MIN_FLOOR + 1
        self.elevator.go_to(target_floor)
        
        # Simuler le trajet complet + ouverture des portes
        total_time = self.elevator.floor_travel_time + self.elevator.door_animation_duration + 0.2
        self.elevator.update(total_time)
        
        assert floor_reached_called is True
        assert doors_opened_called is True
    
    def test_multiple_calls_same_floor(self):
        """Test d'appels multiples au même étage."""
        target_floor = MIN_FLOOR + 1
        
        # Appeler plusieurs fois le même étage
        result1 = self.elevator.call(target_floor)
        result2 = self.elevator.call(target_floor)
        result3 = self.elevator.call(target_floor)
        
        assert result1 is True
        assert result2 is True
        assert result3 is True
        
        # Ne doit y avoir qu'une seule entrée dans la queue
        assert self.elevator.call_queue.count(target_floor) == 1
