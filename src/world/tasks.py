"""
Système de tâches pour A Day at the Office.
Gère les tâches principales et annexes, dépendances, et progression.
"""

import logging
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from src.core.utils import load_json_safe, safe_get

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types de tâches possibles."""
    INTERACTION = "interaction"
    DIALOGUE = "dialogue"
    EXPLORATION = "exploration"
    COLLECTION = "collection"


class TaskStatus(Enum):
    """États possibles d'une tâche."""
    LOCKED = "locked"        # Pas encore disponible (dépendances non remplies)
    AVAILABLE = "available"  # Disponible mais pas commencée
    IN_PROGRESS = "in_progress"  # En cours
    COMPLETED = "completed"  # Terminée


@dataclass
class Task:
    """
    Représente une tâche du jeu.
    """
    id: str
    title: str
    description: str
    task_type: TaskType
    floor: Optional[int] = None
    interactable_id: Optional[str] = None
    npc_id: Optional[str] = None
    reward_points: int = 0
    required: bool = False
    dependencies: List[str] = None
    completion_message: str = ""
    allow_unassigned_completion: bool = True
    # Extensions temporelles et métadonnées
    due_by: Optional[str] = None
    soft_due: Optional[str] = None
    priority: int = 0
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class TaskManager:
    """
    Gestionnaire des tâches du jeu.
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_status: Dict[str, TaskStatus] = {}
        self.completed_tasks: Set[str] = set()
        self.available_tasks: Set[str] = set()
        self.discovered_tasks: Set[str] = set()
        self.offered_tasks: Set[str] = set()
        self.silent_completions: Set[str] = set()
        
        # Statistiques
        self.total_points = 0
        self.main_tasks_completed = 0
        self.side_tasks_completed = 0
        
        logger.info("TaskManager initialized")
    
    def load_from_json(self, file_path) -> bool:
        """
        Charge les tâches depuis un fichier JSON.
        
        Args:
            file_path: Chemin vers le fichier tasks.json
            
        Returns:
            True si le chargement a réussi
        """
        try:
            data = load_json_safe(file_path)
            if not data:
                logger.error(f"Could not load tasks from {file_path}")
                return False
            
            # Charger les tâches principales
            main_tasks = safe_get(data, "main_tasks", [])
            for task_data in main_tasks:
                if isinstance(task_data, dict):
                    task = self._create_task_from_data(task_data, required=True)
                    if task:
                        self.add_task(task)
            
            # Charger les tâches annexes
            side_tasks = safe_get(data, "side_tasks", [])
            for task_data in side_tasks:
                if isinstance(task_data, dict):
                    task = self._create_task_from_data(task_data, required=False)
                    if task:
                        self.add_task(task)
            
            # Calculer les tâches disponibles
            self._update_available_tasks()
            
            logger.info(f"Loaded {len(self.tasks)} tasks")
            return True
            
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            return False
    
    def _create_task_from_data(self, data: Dict[str, Any], required: bool) -> Optional[Task]:
        """
        Crée une tâche à partir des données JSON.
        
        Args:
            data: Données de la tâche
            required: Si la tâche est requise
            
        Returns:
            Tâche créée ou None en cas d'erreur
        """
        try:
            task_id = safe_get(data, "id")
            if not task_id:
                logger.error("Task missing ID")
                return None
            
            # Déterminer le type de tâche
            task_type_str = safe_get(data, "type", "interaction")
            try:
                task_type = TaskType(task_type_str)
            except ValueError:
                logger.warning(f"Unknown task type '{task_type_str}', using INTERACTION")
                task_type = TaskType.INTERACTION
            
            task = Task(
                id=task_id,
                title=safe_get(data, "title", "Tâche sans nom"),
                description=safe_get(data, "description", ""),
                task_type=task_type,
                floor=safe_get(data, "floor"),
                interactable_id=safe_get(data, "interactable_id"),
                npc_id=safe_get(data, "npc_id"),
                reward_points=safe_get(data, "reward_points", 0),
                required=required,
                dependencies=safe_get(data, "dependencies", []),
                completion_message=safe_get(data, "completion_message", "Tâche terminée !"),
                allow_unassigned_completion=bool(safe_get(data, "allow_unassigned_completion", True)),
                due_by=safe_get(data, "due_by"),
                soft_due=safe_get(data, "soft_due"),
                priority=int(safe_get(data, "priority", 0) or 0),
                tags=list(safe_get(data, "tags", []) or [])
            )
            
            return task
            
        except Exception as e:
            logger.error(f"Error creating task from data: {e}")
            return None
    
    def add_task(self, task: Task) -> None:
        """
        Ajoute une tâche au gestionnaire.
        
        Args:
            task: Tâche à ajouter
        """
        self.tasks[task.id] = task
        
        # Déterminer le statut initial
        # Les tâches principales sont toujours disponibles si leurs dépendances sont remplies
        # Les tâches annexes ne deviennent disponibles QUE si (dépendances OK) ET (offertes) OU tag "auto"
        auto = ("auto" in (task.tags or []))
        if self._are_dependencies_met(task):
            if task.required or task.id in self.offered_tasks or auto:
                self.task_status[task.id] = TaskStatus.AVAILABLE
                self.available_tasks.add(task.id)
            else:
                self.task_status[task.id] = TaskStatus.LOCKED
        else:
            self.task_status[task.id] = TaskStatus.LOCKED
        
        logger.debug(f"Task added: {task.id} ({self.task_status[task.id].value})")
    
    def complete_task(self, task_id: str) -> bool:
        """
        Marque une tâche comme terminée.
        
        Args:
            task_id: ID de la tâche
            
        Returns:
            True si la tâche a été marquée comme terminée
        """
        if task_id not in self.tasks:
            logger.warning(f"Task not found: {task_id}")
            return False
        
        if task_id in self.completed_tasks:
            logger.debug(f"Task already completed: {task_id}")
            return False
        
        task = self.tasks[task_id]
        
        # Marquer comme terminée
        self.completed_tasks.add(task_id)
        self.task_status[task_id] = TaskStatus.COMPLETED
        self.available_tasks.discard(task_id)
        
        # Ajouter les points
        self.total_points += task.reward_points
        
        # Compter les tâches par type
        if task.required:
            self.main_tasks_completed += 1
        else:
            self.side_tasks_completed += 1
        
        # Mettre à jour les tâches disponibles (déverrouiller les dépendantes)
        self._update_available_tasks()
        
        logger.info(f"Task completed: {task.title} (+{task.reward_points} points)")
        return True

    def complete_task_unassigned_if_match(self, interactable_or_obj_id: str) -> Optional[str]:
        """
        Marque une tâche comme terminée de façon silencieuse si une action
        correspond à son interactable, même si la tâche n'a pas été offerte.
        
        Args:
            interactable_or_obj_id: ID de l'interactable ou de l'objet du monde
        
        Returns:
            L'ID de la tâche complétée, ou None pour signaler une complétion silencieuse
        """
        # Chercher une tâche correspondante (priorité: interactable_id)
        for task in self.tasks.values():
            if task.interactable_id and task.interactable_id == interactable_or_obj_id:
                if task.id in self.completed_tasks:
                    return None
                if not task.allow_unassigned_completion:
                    return None
                # Compléter silencieusement
                self.completed_tasks.add(task.id)
                self.task_status[task.id] = TaskStatus.COMPLETED
                self.available_tasks.discard(task.id)
                self.silent_completions.add(task.id)
                # Récompenser
                self.total_points += task.reward_points
                if task.required:
                    self.main_tasks_completed += 1
                else:
                    self.side_tasks_completed += 1
                # Débloquer les dépendantes
                self._update_available_tasks()
                logger.info(f"Task silently completed via unassigned action: {task.id}")
                # Retourner None pour laisser l'UI afficher un toast discret
                return None
        return None
    
    def _are_dependencies_met(self, task: Task) -> bool:
        """
        Vérifie si les dépendances d'une tâche sont remplies.
        
        Args:
            task: Tâche à vérifier
            
        Returns:
            True si toutes les dépendances sont remplies
        """
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
        return True
    
    def _update_available_tasks(self) -> None:
        """Met à jour la liste des tâches disponibles."""
        for task_id, task in self.tasks.items():
            current_status = self.task_status.get(task_id, TaskStatus.LOCKED)
            # Une tâche devient disponible si dépendances OK ET (principale OU offerte)
            should_be_available = self._are_dependencies_met(task) and (task.required or task_id in self.offered_tasks)
            if should_be_available and current_status in [TaskStatus.LOCKED, None]:
                self.task_status[task_id] = TaskStatus.AVAILABLE
                self.available_tasks.add(task_id)
                logger.debug(f"Task unlocked: {task.title}")
            elif not should_be_available and current_status == TaskStatus.AVAILABLE:
                self.available_tasks.discard(task_id)
                self.task_status[task_id] = TaskStatus.LOCKED
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Récupère une tâche par son ID.
        
        Args:
            task_id: ID de la tâche
            
        Returns:
            Tâche trouvée ou None
        """
        return self.tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Récupère le statut d'une tâche.
        
        Args:
            task_id: ID de la tâche
            
        Returns:
            Statut de la tâche ou None
        """
        return self.task_status.get(task_id)
    
    def is_task_completed(self, task_id: str) -> bool:
        """
        Vérifie si une tâche est terminée.
        
        Args:
            task_id: ID de la tâche
            
        Returns:
            True si la tâche est terminée
        """
        return task_id in self.completed_tasks
    
    def is_task_available(self, task_id: str) -> bool:
        """
        Vérifie si une tâche est disponible.
        
        Args:
            task_id: ID de la tâche
            
        Returns:
            True si la tâche est disponible
        """
        return task_id in self.available_tasks
    
    def get_available_tasks(self) -> List[Task]:
        """
        Retourne toutes les tâches disponibles.
        
        Returns:
            Liste des tâches disponibles
        """
        return [self.tasks[task_id] for task_id in self.available_tasks if task_id in self.tasks]
    
    def get_completed_tasks(self) -> List[Task]:
        """
        Retourne toutes les tâches terminées.
        
        Returns:
            Liste des tâches terminées
        """
        return [self.tasks[task_id] for task_id in self.completed_tasks if task_id in self.tasks]
    
    def get_main_tasks(self) -> List[Task]:
        """
        Retourne toutes les tâches principales.
        
        Returns:
            Liste des tâches principales
        """
        return [task for task in self.tasks.values() if task.required]
    
    def get_side_tasks(self) -> List[Task]:
        """
        Retourne toutes les tâches annexes.
        
        Returns:
            Liste des tâches annexes
        """
        return [task for task in self.tasks.values() if not task.required]
    
    def get_tasks_for_floor(self, floor: int) -> List[Task]:
        """
        Retourne les tâches disponibles pour un étage.
        
        Args:
            floor: Numéro d'étage
            
        Returns:
            Liste des tâches de cet étage
        """
        floor_tasks = []
        for task in self.get_available_tasks():
            if task.floor == floor:
                floor_tasks.append(task)
        return floor_tasks
    
    def get_task_for_interactable(self, interactable_id: str) -> Optional[Task]:
        """
        Trouve la tâche associée à un objet interactif.
        
        Args:
            interactable_id: ID de l'objet
            
        Returns:
            Tâche trouvée ou None
        """
        cands = [t for t in self.get_available_tasks() if t.interactable_id == interactable_id]
        if not cands:
            return None
        # priorité : required desc, puis priority (plus grand d'abord), puis id
        cands.sort(key=lambda t: (not t.required, -t.priority, t.id))
        return cands[0]
    
    def get_task_for_npc(self, npc_id: str) -> Optional[Task]:
        """
        Trouve la tâche associée à un NPC.
        
        Args:
            npc_id: ID du NPC
            
        Returns:
            Tâche trouvée ou None
        """
        for task in self.get_available_tasks():
            if task.npc_id == npc_id:
                return task
        return None

    def is_task_known(self, task_id: str) -> bool:
        """Vérifie si une tâche est connue (chargée)."""
        return task_id in self.tasks

    def is_task_available(self, task_id: str) -> bool:
        """Vérifie si une tâche est disponible."""
        return self.task_status.get(task_id) == TaskStatus.AVAILABLE

    def offer_task(self, task_id: str) -> None:
        """
        Marque une tâche comme 'offerte' (utile pour les side-tasks qui ne se débloquent
        pas automatiquement). Met à jour son statut si dépendances remplies.
        """
        if task_id not in self.tasks:
            return
        self.offered_tasks.add(task_id)
        self._update_available_tasks()

    # === Extensions DSL/Story ===
    def discover_task(self, task_id: str) -> bool:
        """Marque une tâche comme découverte (sans l'offrir)."""
        if task_id not in self.tasks:
            return False
        if task_id in self.discovered_tasks:
            return False
        self.discovered_tasks.add(task_id)
        logger.debug(f"Task discovered: {task_id}")
        return True

    def offer_task(self, task_id: str) -> bool:
        """
        Offre une tâche (la rend éligible à devenir AVAILABLE si dépendances ok).
        """
        if task_id not in self.tasks:
            return False
        self.offered_tasks.add(task_id)
        # Réévaluer la disponibilité
        self._update_available_tasks()
        logger.debug(f"Task offered: {task_id}")
        return True

    def add_points(self, amount: int) -> None:
        """Ajoute des points au score total."""
        try:
            self.total_points += int(amount)
        except Exception:
            pass
    
    def are_all_main_tasks_completed(self) -> bool:
        """
        Vérifie si toutes les tâches principales sont terminées.
        
        Returns:
            True si toutes les tâches principales sont terminées
        """
        main_tasks = self.get_main_tasks()
        return all(task.id in self.completed_tasks for task in main_tasks)
    
    def are_all_tasks_completed(self) -> bool:
        """
        Vérifie si toutes les tâches sont terminées.
        
        Returns:
            True si toutes les tâches sont terminées
        """
        return len(self.completed_tasks) == len(self.tasks)
    
    def get_completion_percentage(self) -> float:
        """
        Retourne le pourcentage de completion des tâches.
        
        Returns:
            Pourcentage entre 0.0 et 1.0
        """
        if not self.tasks:
            return 1.0
        return len(self.completed_tasks) / len(self.tasks)
    
    def get_main_tasks_completion_percentage(self) -> float:
        """
        Retourne le pourcentage de completion des tâches principales.
        
        Returns:
            Pourcentage entre 0.0 et 1.0
        """
        main_tasks = self.get_main_tasks()
        if not main_tasks:
            return 1.0
        
        completed_main = sum(1 for task in main_tasks if task.id in self.completed_tasks)
        return completed_main / len(main_tasks)
    
    def reset(self) -> None:
        """Remet le gestionnaire de tâches à zéro."""
        self.completed_tasks.clear()
        self.available_tasks.clear()
        self.discovered_tasks.clear()
        self.offered_tasks.clear()
        self.silent_completions.clear()
        self.total_points = 0
        self.main_tasks_completed = 0
        self.side_tasks_completed = 0
        
        # Recalculer les statuts
        for task_id, task in self.tasks.items():
            if self._are_dependencies_met(task) and (task.required or task_id in self.offered_tasks):
                self.task_status[task_id] = TaskStatus.AVAILABLE
                self.available_tasks.add(task_id)
            else:
                self.task_status[task_id] = TaskStatus.LOCKED
        
        logger.info("TaskManager reset")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur les tâches.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        return {
            "total_tasks": len(self.tasks),
            "completed_tasks": len(self.completed_tasks),
            "available_tasks": len(self.available_tasks),
            "main_tasks_completed": self.main_tasks_completed,
            "side_tasks_completed": self.side_tasks_completed,
            "total_points": self.total_points,
            "completion_percentage": self.get_completion_percentage(),
            "main_completion_percentage": self.get_main_tasks_completion_percentage(),
            "all_main_completed": self.are_all_main_tasks_completed(),
            "all_completed": self.are_all_tasks_completed()
        }
