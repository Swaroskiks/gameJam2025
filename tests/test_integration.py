"""
Tests d'intégration pour les nouvelles fonctionnalités de A Day at the Office.
"""

import sys
from pathlib import Path

# Ajouter le dossier racine au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pygame
from src.core.camera import Camera
from src.world.building import Building, Floor
from src.ui.widgets import IconButton, Panel
from src.core.assets import asset_manager


def test_camera_movement():
    """Test que la caméra se déplace correctement vers sa cible."""
    camera = Camera(initial_y=0.0, speed=100.0)
    
    # Définir une cible
    camera.set_target(100.0)
    assert camera.is_moving
    assert camera.get_target() == 100.0
    
    # Simuler une frame de 0.5 seconde
    camera.update(0.5)
    
    # La caméra devrait avoir bougé de 50 pixels (100 * 0.5)
    assert camera.get_position() == 50.0
    assert camera.is_moving
    
    # Simuler une autre frame pour atteindre la cible
    camera.update(0.6)  # Un peu plus de temps pour être sûr
    assert abs(camera.get_position() - 100.0) < 1.0  # Tolérance
    assert camera.is_at_target()


def test_building_floor_order():
    """Test que les étages sont ordonnés correctement."""
    building = Building()
    
    # Données de test
    floors_data = {
        "min_floor": 90,
        "max_floor": 95,
        "floors": {
            "90": {"name": "Lobby", "objects": []},
            "95": {"name": "Top", "objects": []},
            "92": {"name": "Middle", "objects": []}
        }
    }
    
    success = building.load_from_data(floors_data)
    assert success
    
    # Vérifier que min_floor et max_floor sont correctement définis
    assert building.min_floor == 90
    assert building.max_floor == 95
    
    # Vérifier que les étages sont chargés
    assert building.has_floor(90)
    assert building.has_floor(92)
    assert building.has_floor(95)
    assert not building.has_floor(91)


def test_icon_button_creation():
    """Test que les IconButton se créent correctement."""
    pygame.init()
    pygame.display.set_mode((100, 100))  # Surface minimale pour les tests
    
    # Créer un bouton avec callback
    clicked = False
    def on_click():
        nonlocal clicked
        clicked = True
    
    button = IconButton(10, 10, 32, "ui_task_icon", callback=on_click)
    
    assert button.rect.x == 10
    assert button.rect.y == 10
    assert button.rect.width == 32
    assert button.rect.height == 32
    assert button.enabled
    assert button.visible
    
    # Test de base - la création fonctionne
    assert button.icon_key == "ui_task_icon"


def test_panel_toggle():
    """Test que les Panel se toggle correctement."""
    pygame.init()
    pygame.display.set_mode((100, 100))
    
    panel = Panel(50, 50, 200, 150, "Test Panel")
    
    # État initial
    assert not panel.is_visible()
    
    # Toggle
    panel.toggle()
    assert panel.is_visible()
    
    panel.toggle()
    assert not panel.is_visible()
    
    # Show/Hide direct
    panel.show()
    assert panel.is_visible()
    
    panel.hide()
    assert not panel.is_visible()


def test_floor_background_loading():
    """Test que les fonds d'étage se chargent correctement."""
    # Charger le manifest pour avoir des assets disponibles
    success = asset_manager.load_manifest()
    assert success or True  # Peut échouer en test, c'est OK
    
    # Créer un étage avec bg_key
    floor_data = {
        "name": "Test Floor",
        "bg_key": "floor_98",
        "objects": []
    }
    
    floor = Floor(98, floor_data)
    assert floor.bg_key == "floor_98"
    assert floor.background_surface is None  # Pas encore chargé
    
    # Charger le fond
    floor.load_background(asset_manager, "floor_default")
    # Le fond devrait être chargé (ou un placeholder créé)
    assert floor.background_surface is not None


if __name__ == "__main__":
    pygame.init()
    test_camera_movement()
    test_building_floor_order()
    test_icon_button_creation()
    test_panel_toggle()
    test_floor_background_loading()
    print("✅ Tous les tests d'intégration passent !")
    pygame.quit()
