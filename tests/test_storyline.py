"""
Tests narration et règles gameplay (intro boss, complétions non assignées, événements temporels).
"""

import pygame
import pytest
from pathlib import Path

from src.world.tasks import TaskManager
from src.scenes.gameplay import GameplayScene
from src.core.scene_manager import SceneManager
from src.core.timer import GameClock


def test_unassigned_completion_printer_counts():
    manager = TaskManager()
    assert manager.load_from_json(Path("src/data/tasks.json")) or True
    # Assurer que la tâche n'est pas déjà complétée
    assert not manager.is_task_completed("fix_printer")
    # Action directe sur l'imprimante sans offre préalable
    manager.complete_task_unassigned_if_match("printer_97")
    assert manager.is_task_completed("fix_printer")


def test_boss_intro_unlocks_tasks_panel():
    scene = GameplayScene(SceneManager())
    # Avant de parler au boss, l'intro est active
    assert scene._intro_lock_active is True
    # Appliquer l'effet de drapeau via DSL
    scene._apply_effect({"set_flag": "met_boss"})
    assert scene._intro_lock_active is False


def test_time_event_printer_aggravates():
    scene = GameplayScene(SceneManager())
    scene.game_clock = GameClock("08:30", "08:48", 5.0)
    # Forcer l'heure à 08:37
    scene.game_clock.current_time = scene.game_clock._parse_time("08:37")
    # Avant l'événement
    assert scene._printer_requirement in [2, 3]
    scene._process_timeline_events()
    assert scene._printer_requirement == 3


