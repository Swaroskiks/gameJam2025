"""
Configuration pytest pour A Day at the Office.
Fixtures communes et setup des tests.
"""

import pytest
import sys
from pathlib import Path

# Ajouter le dossier src au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_task_data():
    """Données de tâches pour les tests."""
    return {
        "main_tasks": [
            {
                "id": "water_plant",
                "title": "Arroser la plante",
                "description": "La plante du bureau de direction a l'air assoiffée.",
                "type": "interaction",
                "floor": 98,
                "interactable_id": "plant_98",
                "reward_points": 10,
                "dependencies": [],
                "completion_message": "La plante vous remercie."
            },
            {
                "id": "organize_papers",
                "title": "Ranger les papiers",
                "description": "Des documents traînent sur le bureau.",
                "type": "interaction",
                "floor": 98,
                "interactable_id": "papers_98",
                "reward_points": 8,
                "dependencies": [],
                "completion_message": "Les papiers sont classés."
            }
        ],
        "side_tasks": [
            {
                "id": "talk_to_boss",
                "title": "Parler au patron",
                "description": "M. Johnson souhaite vous voir.",
                "type": "dialogue",
                "floor": 98,
                "npc_id": "boss",
                "reward_points": 5,
                "dependencies": ["organize_papers", "water_plant"],
                "completion_message": "M. Johnson semble satisfait."
            }
        ]
    }


@pytest.fixture
def sample_floors_data():
    """Données d'étages pour les tests."""
    return {
        "min_floor": 90,
        "max_floor": 98,
        "elevator_position_x": 64,
        "floor_height": 120,
        "floors": {
            "98": {
                "name": "Direction",
                "rooms": ["office_director", "meeting_room"],
                "interactables": [
                    {
                        "id": "papers_98",
                        "type": "papers",
                        "x": 300,
                        "y": 50,
                        "task_id": "organize_papers"
                    },
                    {
                        "id": "plant_98",
                        "type": "plant",
                        "x": 450,
                        "y": 30,
                        "task_id": "water_plant"
                    }
                ],
                "npcs": [
                    {
                        "id": "boss",
                        "name": "M. Johnson",
                        "x": 200,
                        "y": 60,
                        "dialogue_id": "boss_morning"
                    }
                ]
            },
            "90": {
                "name": "Lobby",
                "rooms": ["lobby", "reception"],
                "interactables": [
                    {
                        "id": "reception_90",
                        "type": "reception_desk",
                        "x": 200,
                        "y": 70,
                        "task_id": "check_badge"
                    }
                ],
                "npcs": [
                    {
                        "id": "guard",
                        "name": "Gardien",
                        "x": 150,
                        "y": 80,
                        "dialogue_id": "guard_morning"
                    }
                ]
            }
        }
    }


@pytest.fixture
def sample_manifest_data():
    """Données de manifest pour les tests."""
    return {
        "version": 1,
        "description": "Test manifest",
        "images": {
            "player_idle": {
                "path": "sprites/player_idle.png",
                "frame_w": 32,
                "frame_h": 48,
                "description": "Joueur au repos"
            },
            "elevator": {
                "path": "sprites/elevator.png",
                "frame_w": 64,
                "frame_h": 128,
                "description": "Cabine d'ascenseur"
            }
        },
        "spritesheets": {
            "player_walk": {
                "path": "sprites/player_walk.png",
                "frame_w": 32,
                "frame_h": 48,
                "fps": 8,
                "frames": 4,
                "description": "Animation marche du joueur"
            }
        },
        "fonts": {
            "ui_font": {
                "path": "fonts/Pixellari.ttf",
                "size": 18,
                "description": "Police UI principale"
            }
        },
        "audio": {
            "sfx": {
                "elevator_ding": {
                    "path": "sfx/ding.wav",
                    "volume": 0.7,
                    "description": "Son ding d'ascenseur"
                }
            },
            "music": {
                "ambient": {
                    "path": "music/ambient.ogg",
                    "volume": 0.3,
                    "loop": True,
                    "description": "Ambiance bureau"
                }
            }
        }
    }
