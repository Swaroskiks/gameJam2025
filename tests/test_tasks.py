"""
Tests pour le système de tâches.
"""

import pytest
from src.world.tasks import Task, TaskManager, TaskType, TaskStatus


class TestTask:
    """Tests pour la classe Task."""
    
    def test_task_creation(self):
        """Test de création d'une tâche."""
        task = Task(
            id="test_task",
            title="Tâche de test",
            description="Description de test",
            task_type=TaskType.INTERACTION,
            reward_points=10,
            required=True
        )
        
        assert task.id == "test_task"
        assert task.title == "Tâche de test"
        assert task.task_type == TaskType.INTERACTION
        assert task.reward_points == 10
        assert task.required is True
        assert task.dependencies == []


class TestTaskManager:
    """Tests pour TaskManager."""
    
    def setup_method(self):
        """Setup pour chaque test."""
        self.manager = TaskManager()
    
    def test_initialization(self):
        """Test de l'initialisation."""
        assert len(self.manager.tasks) == 0
        assert len(self.manager.completed_tasks) == 0
        assert self.manager.total_points == 0
        assert self.manager.main_tasks_completed == 0
        assert self.manager.side_tasks_completed == 0
    
    def test_add_task(self):
        """Test d'ajout de tâche."""
        task = Task(
            id="task1",
            title="Première tâche",
            description="Test",
            task_type=TaskType.INTERACTION,
            required=True
        )
        
        self.manager.add_task(task)
        
        assert "task1" in self.manager.tasks
        assert self.manager.get_task_status("task1") == TaskStatus.AVAILABLE
        assert "task1" in self.manager.available_tasks
    
    def test_complete_task(self):
        """Test de completion de tâche."""
        task = Task(
            id="task1",
            title="Première tâche",
            description="Test",
            task_type=TaskType.INTERACTION,
            reward_points=15,
            required=True
        )
        
        self.manager.add_task(task)
        success = self.manager.complete_task("task1")
        
        assert success is True
        assert "task1" in self.manager.completed_tasks
        assert self.manager.get_task_status("task1") == TaskStatus.COMPLETED
        assert self.manager.total_points == 15
        assert self.manager.main_tasks_completed == 1
    
    def test_task_dependencies(self):
        """Test des dépendances entre tâches."""
        # Tâche de base
        task1 = Task(
            id="task1",
            title="Tâche de base",
            description="Première tâche",
            task_type=TaskType.INTERACTION,
            required=True
        )
        
        # Tâche dépendante
        task2 = Task(
            id="task2",
            title="Tâche dépendante",
            description="Dépend de task1",
            task_type=TaskType.INTERACTION,
            dependencies=["task1"],
            required=True
        )
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        
        # task1 doit être disponible, task2 verrouillée
        assert self.manager.get_task_status("task1") == TaskStatus.AVAILABLE
        assert self.manager.get_task_status("task2") == TaskStatus.LOCKED
        
        # Compléter task1 doit déverrouiller task2
        self.manager.complete_task("task1")
        assert self.manager.get_task_status("task2") == TaskStatus.AVAILABLE
    
    def test_main_vs_side_tasks(self):
        """Test de la distinction tâches principales/annexes."""
        main_task = Task(
            id="main1",
            title="Tâche principale",
            description="Test",
            task_type=TaskType.INTERACTION,
            required=True
        )
        
        side_task = Task(
            id="side1",
            title="Tâche annexe",
            description="Test",
            task_type=TaskType.DIALOGUE,
            required=False
        )
        
        self.manager.add_task(main_task)
        self.manager.add_task(side_task)
        
        main_tasks = self.manager.get_main_tasks()
        side_tasks = self.manager.get_side_tasks()
        
        assert len(main_tasks) == 1
        assert len(side_tasks) == 1
        assert main_tasks[0].id == "main1"
        assert side_tasks[0].id == "side1"
    
    def test_completion_percentage(self):
        """Test du calcul de pourcentage de completion."""
        # Ajouter 4 tâches
        for i in range(4):
            task = Task(
                id=f"task{i}",
                title=f"Tâche {i}",
                description="Test",
                task_type=TaskType.INTERACTION,
                required=(i < 2)  # 2 principales, 2 annexes
            )
            self.manager.add_task(task)
        
        # Compléter 2 tâches
        self.manager.complete_task("task0")
        self.manager.complete_task("task2")
        
        assert self.manager.get_completion_percentage() == 0.5  # 2/4
        assert self.manager.get_main_tasks_completion_percentage() == 0.5  # 1/2
    
    def test_all_tasks_completed(self):
        """Test de vérification de completion totale."""
        task1 = Task(
            id="task1",
            title="Tâche 1",
            description="Test",
            task_type=TaskType.INTERACTION,
            required=True
        )
        
        task2 = Task(
            id="task2",
            title="Tâche 2", 
            description="Test",
            task_type=TaskType.INTERACTION,
            required=True
        )
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        
        assert not self.manager.are_all_main_tasks_completed()
        assert not self.manager.are_all_tasks_completed()
        
        self.manager.complete_task("task1")
        assert not self.manager.are_all_main_tasks_completed()
        
        self.manager.complete_task("task2")
        assert self.manager.are_all_main_tasks_completed()
        assert self.manager.are_all_tasks_completed()
    
    def test_get_available_tasks(self):
        """Test de récupération des tâches disponibles."""
        # Tâche disponible
        task1 = Task(
            id="task1",
            title="Disponible",
            description="Test",
            task_type=TaskType.INTERACTION
        )
        
        # Tâche verrouillée
        task2 = Task(
            id="task2",
            title="Verrouillée",
            description="Test",
            task_type=TaskType.INTERACTION,
            dependencies=["task1"]
        )
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        
        available = self.manager.get_available_tasks()
        assert len(available) == 1
        assert available[0].id == "task1"
    
    def test_reset(self):
        """Test de remise à zéro."""
        task = Task(
            id="task1",
            title="Test",
            description="Test",
            task_type=TaskType.INTERACTION,
            reward_points=10
        )
        
        self.manager.add_task(task)
        self.manager.complete_task("task1")
        
        # Vérifier qu'on a des données
        assert self.manager.total_points > 0
        assert len(self.manager.completed_tasks) > 0
        
        # Reset
        self.manager.reset()
        
        # Vérifier la remise à zéro
        assert self.manager.total_points == 0
        assert len(self.manager.completed_tasks) == 0
        assert self.manager.main_tasks_completed == 0
        assert self.manager.side_tasks_completed == 0
        
        # Les tâches doivent être recalculées
        assert self.manager.get_task_status("task1") == TaskStatus.AVAILABLE
    
    def test_get_stats(self):
        """Test des statistiques."""
        task1 = Task(
            id="task1",
            title="Principale",
            description="Test",
            task_type=TaskType.INTERACTION,
            reward_points=10,
            required=True
        )
        
        task2 = Task(
            id="task2",
            title="Annexe",
            description="Test",
            task_type=TaskType.DIALOGUE,
            reward_points=5,
            required=False
        )
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        self.manager.complete_task("task1")
        
        stats = self.manager.get_stats()
        
        assert stats["total_tasks"] == 2
        assert stats["completed_tasks"] == 1
        assert stats["available_tasks"] == 1  # task2 encore disponible
        assert stats["main_tasks_completed"] == 1
        assert stats["side_tasks_completed"] == 0
        assert stats["total_points"] == 10
        assert stats["completion_percentage"] == 0.5
        assert stats["main_completion_percentage"] == 1.0
        assert stats["all_main_completed"] is True
        assert stats["all_completed"] is False
    
    def test_nonexistent_task_operations(self):
        """Test des opérations sur des tâches inexistantes."""
        # Compléter une tâche qui n'existe pas
        result = self.manager.complete_task("nonexistent")
        assert result is False
        
        # Récupérer une tâche inexistante
        task = self.manager.get_task("nonexistent")
        assert task is None
        
        # Statut d'une tâche inexistante
        status = self.manager.get_task_status("nonexistent")
        assert status is None
