"""
Interface utilisateur overlay pour A Day at the Office.
Gère l'affichage de l'horloge, des tâches, et des informations contextuelles.
"""

import logging
from typing import List, Optional, Tuple, Dict, Any
import pygame
from src.settings import WIDTH, HEIGHT, UI_BACKGROUND, UI_TEXT, UI_PANEL
from src.core.assets import asset_manager
from src.core.utils import draw_text_centered, create_text_surface
from src.world.tasks import Task, TaskStatus
from src.ui.widgets import IconButton, Panel

logger = logging.getLogger(__name__)


class HUD:
    """
    Interface utilisateur principale (Head-Up Display).
    """
    
    def __init__(self):
        self.visible = True
        self.font_ui = None
        self.font_small = None
        self.font_title = None
        
        # Positions des éléments
        self.clock_pos = (WIDTH - 150, 30)
        self.floor_pos = (WIDTH // 2, 20)
        self.interaction_hint_pos = (WIDTH // 2, HEIGHT - 50)
        
        # État
        self.show_interaction_hint_flag = False
        self.interaction_hint_text = ""
        self.current_floor_name = ""
        
        # Nouveau système d'icône des tâches
        self.task_icon = IconButton(
            WIDTH - 60, 80, 40, "ui_task_icon",
            callback=self._toggle_tasks_panel,
            tooltip="Afficher les tâches (T)"
        )
        self.tasks_panel = Panel(
            WIDTH - 350, 120, 300, 400,
            title="Tâches"
        )
        
        logger.info("HUD initialized")
    
    def load_fonts(self) -> None:
        """Charge les polices nécessaires."""
        try:
            self.font_ui = asset_manager.get_font("ui_font")
            self.font_small = asset_manager.get_font("body_font")
            self.font_title = asset_manager.get_font("title_font")
        except Exception as e:
            logger.error(f"Error loading HUD fonts: {e}")
    
    def draw_clock(self, surface: pygame.Surface, time_str: str, progress: float = 0.0) -> None:
        """
        Dessine l'horloge diégétique.
        
        Args:
            surface: Surface de destination
            time_str: Heure actuelle "HH:MM"
            progress: Progression de 0.0 à 1.0
        """
        if not self.visible or not self.font_ui:
            return
        
        # Panneau de fond
        panel_width, panel_height = 140, 80
        panel_rect = pygame.Rect(
            self.clock_pos[0] - panel_width // 2,
            self.clock_pos[1] - 10,
            panel_width,
            panel_height
        )
        
        # Fond semi-transparent
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill(UI_PANEL)
        surface.blit(panel_surface, panel_rect.topleft)
        
        # Bordure
        pygame.draw.rect(surface, UI_TEXT, panel_rect, 2)
        
        # Texte de l'heure
        draw_text_centered(surface, time_str, self.font_ui, UI_TEXT, 
                          (self.clock_pos[0], self.clock_pos[1] + 15))
        
        # Barre de progression
        if progress > 0.0:
            bar_width = panel_width - 20
            bar_height = 6
            bar_x = panel_rect.x + 10
            bar_y = panel_rect.y + panel_height - 20
            
            # Fond de la barre
            bar_bg = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
            pygame.draw.rect(surface, (50, 50, 50), bar_bg)
            
            # Progression
            progress_width = int(bar_width * progress)
            if progress_width > 0:
                progress_rect = pygame.Rect(bar_x, bar_y, progress_width, bar_height)
                # Couleur qui change selon la progression
                if progress < 0.5:
                    color = (0, 255, 0)  # Vert
                elif progress < 0.8:
                    color = (255, 255, 0)  # Jaune
                else:
                    color = (255, 100, 0)  # Orange/Rouge
                
                pygame.draw.rect(surface, color, progress_rect)
    
    def _toggle_tasks_panel(self) -> None:
        """Toggle l'affichage du panneau des tâches."""
        self.tasks_panel.toggle()
        logger.debug(f"Tasks panel toggled: {'visible' if self.tasks_panel.is_visible() else 'hidden'}")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Gère les événements UI.
        
        Args:
            event: Événement pygame
            
        Returns:
            True si l'événement a été consommé
        """
        # Gestion de la touche T pour toggle des tâches
        if event.type == pygame.KEYDOWN and event.key == pygame.K_t:
            self._toggle_tasks_panel()
            return True
        
        # Gestion des événements du panneau des tâches (priorité)
        if self.tasks_panel.handle_event(event):
            return True
        
        # Gestion de l'icône des tâches
        if self.task_icon.handle_event(event):
            return True
        
        return False
    
    def draw_tasks(self, surface: pygame.Surface, tasks: List[Task], 
                   task_statuses: Dict[str, TaskStatus]) -> None:
        """
        Dessine l'icône des tâches et le panneau flottant si visible.
        
        Args:
            surface: Surface de destination
            tasks: Liste des tâches à afficher
            task_statuses: Statuts des tâches
        """
        if not self.visible:
            return
        
        # Dessiner l'icône des tâches
        self.task_icon.draw(surface)
        
        # Dessiner le panneau des tâches s'il est visible
        if self.tasks_panel.is_visible() and tasks and self.font_small:
            self.tasks_panel.draw(surface)
            
            # Dessiner le contenu des tâches dans le panneau
            content_rect = self.tasks_panel.get_content_rect()
            y_offset = content_rect.y + 10
            
            # Séparer les tâches principales et annexes
            main_tasks = [t for t in tasks if t.required]
            side_tasks = [t for t in tasks if not t.required]
            
            # Tâches principales
            if main_tasks and y_offset < content_rect.bottom - 40:
                title_surface = self.font_ui.render("Principales", True, UI_TEXT)
                surface.blit(title_surface, (content_rect.x + 5, y_offset))
                y_offset += 25
                
                for task in main_tasks:
                    if y_offset + 20 > content_rect.bottom:
                        break
                    status = task_statuses.get(task.id, TaskStatus.LOCKED)
                    self._draw_task_item_in_panel(surface, task, status, content_rect.x + 5, y_offset)
                    y_offset += 20
                
                y_offset += 10
            
            # Tâches annexes (seulement les disponibles/terminées)
            available_side_tasks = [t for t in side_tasks 
                                   if task_statuses.get(t.id) in [TaskStatus.AVAILABLE, TaskStatus.COMPLETED]]
            
            if available_side_tasks and y_offset < content_rect.bottom - 40:
                title_surface = self.font_small.render("Annexes", True, UI_TEXT)
                surface.blit(title_surface, (content_rect.x + 5, y_offset))
                y_offset += 20
                
                for task in available_side_tasks[:5]:  # Limiter pour l'espace
                    if y_offset + 18 > content_rect.bottom:
                        break
                    status = task_statuses.get(task.id, TaskStatus.LOCKED)
                    self._draw_task_item_in_panel(surface, task, status, content_rect.x + 5, y_offset)
                    y_offset += 18
    
    def _draw_task_item_in_panel(self, surface: pygame.Surface, task: Task, status: TaskStatus,
                                x: int, y: int) -> None:
        """
        Dessine une ligne de tâche dans le panneau.
        
        Args:
            surface: Surface de destination
            task: Tâche à dessiner
            status: Statut de la tâche
            x: Position X
            y: Position Y
        """
        # Icône de statut
        if status == TaskStatus.COMPLETED:
            icon = "✓"
            color = (0, 255, 0)  # Vert
        elif status == TaskStatus.IN_PROGRESS:
            icon = "•"
            color = (255, 255, 0)  # Jaune
        elif status == TaskStatus.AVAILABLE:
            icon = "•"
            color = UI_TEXT
        else:
            icon = "○"
            color = (128, 128, 128)  # Gris
        
        # Texte de la tâche (tronqué si nécessaire)
        task_text = f"{icon} {task.title}"
        if len(task_text) > 35:  # Limite pour le panneau
            task_text = task_text[:32] + "..."
        
        task_surface = self.font_small.render(task_text, True, color)
        surface.blit(task_surface, (x, y))
    
    def _draw_task_item(self, surface: pygame.Surface, task: Task, status: TaskStatus,
                       x: int, y: int) -> None:
        """
        Dessine une ligne de tâche.
        
        Args:
            surface: Surface de destination
            task: Tâche à dessiner
            status: Statut de la tâche
            x: Position X
            y: Position Y
        """
        # Icône de statut
        if status == TaskStatus.COMPLETED:
            icon = "✓"
            color = (0, 255, 0)
        elif status == TaskStatus.AVAILABLE:
            icon = "•"
            color = UI_TEXT
        elif status == TaskStatus.IN_PROGRESS:
            icon = "◐"
            color = (255, 255, 0)
        else:  # LOCKED
            icon = "○"
            color = (100, 100, 100)
        
        # Dessiner l'icône
        icon_surface = self.font_small.render(icon, True, color)
        surface.blit(icon_surface, (x, y))
        
        # Dessiner le titre de la tâche
        title_color = color if status != TaskStatus.LOCKED else (100, 100, 100)
        title_surface = self.font_small.render(task.title, True, title_color)
        surface.blit(title_surface, (x + 15, y))
    
    def draw_floor_indicator(self, surface: pygame.Surface, floor_number: int, 
                            floor_name: str) -> None:
        """
        Dessine l'indicateur d'étage.
        
        Args:
            surface: Surface de destination
            floor_number: Numéro d'étage
            floor_name: Nom de l'étage
        """
        if not self.visible or not self.font_ui:
            return
        
        floor_text = f"Étage {floor_number}"
        if floor_name:
            floor_text += f" - {floor_name}"
        
        # Panneau de fond
        text_width = self.font_ui.size(floor_text)[0]
        panel_width = text_width + 20
        panel_height = 40
        
        panel_rect = pygame.Rect(
            self.floor_pos[0] - panel_width // 2,
            self.floor_pos[1] - 5,
            panel_width,
            panel_height
        )
        
        # Fond semi-transparent
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill(UI_PANEL)
        surface.blit(panel_surface, panel_rect.topleft)
        
        # Bordure
        pygame.draw.rect(surface, UI_TEXT, panel_rect, 1)
        
        # Texte
        draw_text_centered(surface, floor_text, self.font_ui, UI_TEXT, self.floor_pos)
    
    def draw_interaction_hint(self, surface: pygame.Surface) -> None:
        """
        Dessine l'indication d'interaction.
        
        Args:
            surface: Surface de destination
        """
        if not self.visible or not self.show_interaction_hint_flag or not self.font_small:
            return
        
        text = self.interaction_hint_text or "E : Interagir"
        
        # Fond semi-transparent
        text_width = self.font_small.size(text)[0]
        panel_width = text_width + 20
        panel_height = 30
        
        panel_rect = pygame.Rect(
            self.interaction_hint_pos[0] - panel_width // 2,
            self.interaction_hint_pos[1] - panel_height // 2,
            panel_width,
            panel_height
        )
        
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill(UI_BACKGROUND)
        surface.blit(panel_surface, panel_rect.topleft)
        
        # Bordure
        pygame.draw.rect(surface, UI_TEXT, panel_rect, 2)
        
        # Texte
        draw_text_centered(surface, text, self.font_small, UI_TEXT, self.interaction_hint_pos)
    
    def show_interaction_hint(self, text: str = "E : Interagir") -> None:
        """
        Affiche l'indication d'interaction.
        
        Args:
            text: Texte à afficher
        """
        self.show_interaction_hint_flag = True
        self.interaction_hint_text = text
    
    def hide_interaction_hint(self) -> None:
        """Cache l'indication d'interaction."""
        self.show_interaction_hint_flag = False
        self.interaction_hint_text = ""
    
    def set_visible(self, visible: bool) -> None:
        """
        Définit la visibilité du HUD.
        
        Args:
            visible: True pour afficher, False pour cacher
        """
        self.visible = visible
    
    def is_visible(self) -> bool:
        """Retourne la visibilité du HUD."""
        return self.visible


class NotificationManager:
    """
    Gestionnaire des notifications temporaires.
    """
    
    def __init__(self):
        self.notifications: List[Dict[str, Any]] = []
        self.font = None
        
        logger.info("NotificationManager initialized")
    
    def load_fonts(self) -> None:
        """Charge les polices nécessaires."""
        try:
            self.font = asset_manager.get_font("ui_font")
        except Exception as e:
            logger.error(f"Error loading notification fonts: {e}")
    
    def add_notification(self, text: str, duration: float = 3.0, 
                        color: Tuple[int, int, int] = UI_TEXT) -> None:
        """
        Ajoute une notification.
        
        Args:
            text: Texte de la notification
            duration: Durée d'affichage en secondes
            color: Couleur du texte
        """
        notification = {
            "text": text,
            "duration": duration,
            "remaining_time": duration,
            "color": color,
            "alpha": 255
        }
        
        self.notifications.append(notification)
        logger.debug(f"Notification added: {text}")
    
    def update(self, dt: float) -> None:
        """
        Met à jour les notifications.
        
        Args:
            dt: Temps écoulé
        """
        # Mettre à jour le temps restant
        for notification in self.notifications[:]:
            notification["remaining_time"] -= dt
            
            # Calculer l'alpha pour le fade out
            if notification["remaining_time"] <= 1.0:
                notification["alpha"] = int(255 * (notification["remaining_time"] / 1.0))
            
            # Supprimer si expirée
            if notification["remaining_time"] <= 0:
                self.notifications.remove(notification)
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Dessine toutes les notifications.
        
        Args:
            surface: Surface de destination
        """
        if not self.font or not self.notifications:
            return
        
        y_offset = HEIGHT - 150  # Commencer en bas
        
        for notification in reversed(self.notifications):  # Plus récentes en bas
            text = notification["text"]
            color = (*notification["color"], notification["alpha"])
            
            # Créer la surface de texte avec alpha
            text_surface = self.font.render(text, True, notification["color"])
            text_surface.set_alpha(notification["alpha"])
            
            # Fond semi-transparent
            text_width, text_height = text_surface.get_size()
            panel_width = text_width + 20
            panel_height = text_height + 10
            
            panel_rect = pygame.Rect(
                WIDTH // 2 - panel_width // 2,
                y_offset - panel_height // 2,
                panel_width,
                panel_height
            )
            
            # Fond avec alpha
            panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            panel_surface.fill((*UI_PANEL[:3], notification["alpha"] // 2))
            surface.blit(panel_surface, panel_rect.topleft)
            
            # Texte
            text_rect = text_surface.get_rect(center=panel_rect.center)
            surface.blit(text_surface, text_rect)
            
            y_offset -= panel_height + 5
    
    def clear_all(self) -> None:
        """Supprime toutes les notifications."""
        self.notifications.clear()
        logger.debug("All notifications cleared")


class ProgressBar:
    """
    Barre de progression générique.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int = 20):
        self.rect = pygame.Rect(x, y, width, height)
        self.progress = 0.0  # 0.0 à 1.0
        self.color_bg = (50, 50, 50)
        self.color_fill = (0, 255, 0)
        self.color_border = UI_TEXT
        self.visible = True
    
    def set_progress(self, progress: float) -> None:
        """
        Définit le progrès.
        
        Args:
            progress: Valeur entre 0.0 et 1.0
        """
        self.progress = max(0.0, min(1.0, progress))
    
    def set_colors(self, bg: Tuple[int, int, int], fill: Tuple[int, int, int], 
                   border: Tuple[int, int, int] = UI_TEXT) -> None:
        """
        Définit les couleurs de la barre.
        
        Args:
            bg: Couleur de fond
            fill: Couleur de remplissage
            border: Couleur de bordure
        """
        self.color_bg = bg
        self.color_fill = fill
        self.color_border = border
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Dessine la barre de progression.
        
        Args:
            surface: Surface de destination
        """
        if not self.visible:
            return
        
        # Fond
        pygame.draw.rect(surface, self.color_bg, self.rect)
        
        # Progression
        if self.progress > 0:
            fill_width = int(self.rect.width * self.progress)
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(surface, self.color_fill, fill_rect)
        
        # Bordure
        pygame.draw.rect(surface, self.color_border, self.rect, 2)
    
    def set_visible(self, visible: bool) -> None:
        """Définit la visibilité."""
        self.visible = visible
