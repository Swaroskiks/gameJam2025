"""
Composants UI réutilisables pour A Day at the Office.
Boutons, menus, panneaux et autres widgets génériques.
"""

import logging
from typing import Optional, Callable, List, Tuple, Dict, Any
from enum import Enum
import pygame
from src.settings import UI_BACKGROUND, UI_HOVER, UI_TEXT, UI_PANEL
from src.core.assets import asset_manager
from src.core.utils import draw_text_centered, point_in_rect

logger = logging.getLogger(__name__)


class ButtonState(Enum):
    """États possibles d'un bouton."""
    NORMAL = "normal"
    HOVER = "hover"
    PRESSED = "pressed"
    DISABLED = "disabled"


class Button:
    """
    Bouton cliquable générique.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 callback: Optional[Callable[[], None]] = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.state = ButtonState.NORMAL
        self.enabled = True
        self.visible = True
        
        # Couleurs par état
        self.colors = {
            ButtonState.NORMAL: UI_PANEL,
            ButtonState.HOVER: UI_HOVER,
            ButtonState.PRESSED: (150, 0, 0, 200),
            ButtonState.DISABLED: (80, 80, 80, 100)
        }
        
        self.text_color = UI_TEXT
        self.border_color = UI_TEXT
        self.font = None
        
        logger.debug(f"Button created: '{text}' at ({x}, {y})")
    
    def load_font(self) -> None:
        """Charge la police du bouton."""
        try:
            self.font = asset_manager.get_font("ui_font")
        except Exception as e:
            logger.error(f"Error loading button font: {e}")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Gère un événement pygame.
        
        Args:
            event: Événement à traiter
            
        Returns:
            True si l'événement a été consommé
        """
        if not self.enabled or not self.visible:
            return False
        
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(mouse_pos):
                if self.state == ButtonState.NORMAL:
                    self.state = ButtonState.HOVER
            else:
                if self.state == ButtonState.HOVER:
                    self.state = ButtonState.NORMAL
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(mouse_pos):
                self.state = ButtonState.PRESSED
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.state == ButtonState.PRESSED:
                if self.rect.collidepoint(mouse_pos):
                    # Clic réussi
                    if self.callback:
                        try:
                            self.callback()
                        except Exception as e:
                            logger.error(f"Error in button callback: {e}")
                    self.state = ButtonState.HOVER
                else:
                    self.state = ButtonState.NORMAL
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Dessine le bouton.
        
        Args:
            surface: Surface de destination
        """
        if not self.visible:
            return
        
        # Déterminer l'état d'affichage
        display_state = ButtonState.DISABLED if not self.enabled else self.state
        
        # Fond du bouton
        color = self.colors.get(display_state, self.colors[ButtonState.NORMAL])
        button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        button_surface.fill(color)
        surface.blit(button_surface, self.rect.topleft)
        
        # Bordure
        border_width = 3 if display_state == ButtonState.PRESSED else 2
        pygame.draw.rect(surface, self.border_color, self.rect, border_width)
        
        # Texte
        if self.font:
            text_color = self.text_color if self.enabled else (100, 100, 100)
            draw_text_centered(surface, self.text, self.font, text_color, self.rect.center)
    
    def set_enabled(self, enabled: bool) -> None:
        """Active ou désactive le bouton."""
        self.enabled = enabled
        if not enabled:
            self.state = ButtonState.DISABLED
        else:
            self.state = ButtonState.NORMAL
    
    def set_visible(self, visible: bool) -> None:
        """Définit la visibilité du bouton."""
        self.visible = visible
    
    def set_text(self, text: str) -> None:
        """Change le texte du bouton."""
        self.text = text


class Panel:
    """
    Panneau d'interface générique.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 title: str = "", background_alpha: int = 140):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.background_alpha = background_alpha
        self.visible = True
        
        # Couleurs
        self.background_color = (*UI_PANEL[:3], background_alpha)
        self.border_color = UI_TEXT
        self.title_color = UI_TEXT
        
        # Fonts
        self.title_font = None
        self.content_font = None
        
        # Contenu
        self.content_lines: List[str] = []
        
        logger.debug(f"Panel created: '{title}' at ({x}, {y})")
    
    def load_fonts(self) -> None:
        """Charge les polices du panneau."""
        try:
            self.title_font = asset_manager.get_font("ui_font")
            self.content_font = asset_manager.get_font("body_font")
        except Exception as e:
            logger.error(f"Error loading panel fonts: {e}")
    
    def set_content(self, lines: List[str]) -> None:
        """
        Définit le contenu du panneau.
        
        Args:
            lines: Lignes de texte à afficher
        """
        self.content_lines = lines.copy()
    
    def add_content_line(self, line: str) -> None:
        """
        Ajoute une ligne de contenu.
        
        Args:
            line: Ligne à ajouter
        """
        self.content_lines.append(line)
    
    def clear_content(self) -> None:
        """Vide le contenu du panneau."""
        self.content_lines.clear()
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Dessine le panneau.
        
        Args:
            surface: Surface de destination
        """
        if not self.visible:
            return
        
        # Fond
        panel_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel_surface.fill(self.background_color)
        surface.blit(panel_surface, self.rect.topleft)
        
        # Bordure
        pygame.draw.rect(surface, self.border_color, self.rect, 2)
        
        # Titre
        y_offset = self.rect.y + 10
        if self.title and self.title_font:
            title_surface = self.title_font.render(self.title, True, self.title_color)
            title_rect = title_surface.get_rect(centerx=self.rect.centerx, y=y_offset)
            surface.blit(title_surface, title_rect)
            y_offset += title_surface.get_height() + 10
        
        # Contenu
        if self.content_lines and self.content_font:
            line_height = self.content_font.get_height()
            for line in self.content_lines:
                if y_offset + line_height > self.rect.bottom - 10:
                    break  # Pas assez de place
                
                line_surface = self.content_font.render(line, True, UI_TEXT)
                surface.blit(line_surface, (self.rect.x + 10, y_offset))
                y_offset += line_height + 2
    
    def set_visible(self, visible: bool) -> None:
        """Définit la visibilité du panneau."""
        self.visible = visible


class Menu:
    """
    Menu avec options sélectionnables.
    """
    
    def __init__(self, x: int, y: int, width: int, title: str = ""):
        self.x = x
        self.y = y
        self.width = width
        self.title = title
        self.options: List[Dict[str, Any]] = []
        self.selected_index = 0
        self.visible = True
        self.enabled = True
        
        # Styling
        self.item_height = 40
        self.padding = 10
        self.background_color = UI_PANEL
        self.selected_color = UI_HOVER
        self.text_color = UI_TEXT
        self.border_color = UI_TEXT
        
        # Fonts
        self.title_font = None
        self.item_font = None
        
        logger.debug(f"Menu created: '{title}' at ({x}, {y})")
    
    def load_fonts(self) -> None:
        """Charge les polices du menu."""
        try:
            self.title_font = asset_manager.get_font("ui_font")
            self.item_font = asset_manager.get_font("body_font")
        except Exception as e:
            logger.error(f"Error loading menu fonts: {e}")
    
    def add_option(self, text: str, callback: Optional[Callable[[], None]] = None,
                   enabled: bool = True, data: Any = None) -> None:
        """
        Ajoute une option au menu.
        
        Args:
            text: Texte de l'option
            callback: Fonction à appeler si sélectionnée
            enabled: Si l'option est activée
            data: Données associées à l'option
        """
        option = {
            "text": text,
            "callback": callback,
            "enabled": enabled,
            "data": data
        }
        self.options.append(option)
    
    def clear_options(self) -> None:
        """Vide toutes les options."""
        self.options.clear()
        self.selected_index = 0
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Gère un événement pygame.
        
        Args:
            event: Événement à traiter
            
        Returns:
            True si l'événement a été consommé
        """
        if not self.enabled or not self.visible or not self.options:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)
                return True
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self.activate_selected()
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            item_index = self._get_item_at_position(mouse_pos)
            if item_index is not None:
                self.selected_index = item_index
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                item_index = self._get_item_at_position(mouse_pos)
                if item_index is not None:
                    self.selected_index = item_index
                    self.activate_selected()
                    return True
        
        return False
    
    def _get_item_at_position(self, pos: Tuple[int, int]) -> Optional[int]:
        """
        Trouve l'index de l'option à une position donnée.
        
        Args:
            pos: Position (x, y)
            
        Returns:
            Index de l'option ou None
        """
        start_y = self.y
        if self.title:
            start_y += 30  # Espace pour le titre
        
        for i, option in enumerate(self.options):
            item_rect = pygame.Rect(
                self.x,
                start_y + i * self.item_height,
                self.width,
                self.item_height
            )
            
            if point_in_rect(pos, item_rect):
                return i
        
        return None
    
    def activate_selected(self) -> None:
        """Active l'option sélectionnée."""
        if 0 <= self.selected_index < len(self.options):
            option = self.options[self.selected_index]
            
            if option["enabled"] and option["callback"]:
                try:
                    option["callback"]()
                except Exception as e:
                    logger.error(f"Error in menu callback: {e}")
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Dessine le menu.
        
        Args:
            surface: Surface de destination
        """
        if not self.visible:
            return
        
        y_offset = self.y
        
        # Titre
        if self.title and self.title_font:
            title_surface = self.title_font.render(self.title, True, self.text_color)
            title_rect = title_surface.get_rect(centerx=self.x + self.width // 2, y=y_offset)
            surface.blit(title_surface, title_rect)
            y_offset += 30
        
        # Options
        if self.item_font:
            for i, option in enumerate(self.options):
                item_rect = pygame.Rect(self.x, y_offset, self.width, self.item_height)
                
                # Fond de l'option
                if i == self.selected_index:
                    # Option sélectionnée
                    selected_surface = pygame.Surface((self.width, self.item_height), pygame.SRCALPHA)
                    selected_surface.fill(self.selected_color)
                    surface.blit(selected_surface, item_rect.topleft)
                
                # Bordure pour l'option sélectionnée
                if i == self.selected_index:
                    pygame.draw.rect(surface, self.border_color, item_rect, 2)
                
                # Texte
                text_color = self.text_color if option["enabled"] else (100, 100, 100)
                text_surface = self.item_font.render(option["text"], True, text_color)
                text_rect = text_surface.get_rect(
                    x=item_rect.x + self.padding,
                    centery=item_rect.centery
                )
                surface.blit(text_surface, text_rect)
                
                y_offset += self.item_height
    
    def set_selected_index(self, index: int) -> None:
        """
        Définit l'index sélectionné.
        
        Args:
            index: Nouvel index
        """
        if 0 <= index < len(self.options):
            self.selected_index = index
    
    def get_selected_option(self) -> Optional[Dict[str, Any]]:
        """Retourne l'option actuellement sélectionnée."""
        if 0 <= self.selected_index < len(self.options):
            return self.options[self.selected_index]
        return None
    
    def set_visible(self, visible: bool) -> None:
        """Définit la visibilité du menu."""
        self.visible = visible
    
    def set_enabled(self, enabled: bool) -> None:
        """Active ou désactive le menu."""
        self.enabled = enabled


class TextInput:
    """
    Champ de saisie de texte.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int = 30,
                 placeholder: str = "", max_length: int = 50):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.placeholder = placeholder
        self.max_length = max_length
        self.active = False
        self.visible = True
        self.enabled = True
        
        # Curseur
        self.cursor_pos = 0
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.cursor_blink_rate = 0.5
        
        # Couleurs
        self.background_color = (255, 255, 255, 200)
        self.active_color = (255, 255, 255, 255)
        self.border_color = UI_TEXT
        self.text_color = (0, 0, 0)
        self.placeholder_color = (128, 128, 128)
        
        self.font = None
        
        logger.debug(f"TextInput created at ({x}, {y})")
    
    def load_font(self) -> None:
        """Charge la police du champ de texte."""
        try:
            self.font = asset_manager.get_font("body_font")
        except Exception as e:
            logger.error(f"Error loading text input font: {e}")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Gère un événement pygame.
        
        Args:
            event: Événement à traiter
            
        Returns:
            True si l'événement a été consommé
        """
        if not self.enabled or not self.visible:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Vérifier si on clique sur le champ
                if self.rect.collidepoint(event.pos):
                    self.active = True
                    return True
                else:
                    self.active = False
        
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                if self.cursor_pos > 0:
                    self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                    self.cursor_pos -= 1
                return True
            elif event.key == pygame.K_DELETE:
                if self.cursor_pos < len(self.text):
                    self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
                return True
            elif event.key == pygame.K_LEFT:
                self.cursor_pos = max(0, self.cursor_pos - 1)
                return True
            elif event.key == pygame.K_RIGHT:
                self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
                return True
            elif event.key == pygame.K_HOME:
                self.cursor_pos = 0
                return True
            elif event.key == pygame.K_END:
                self.cursor_pos = len(self.text)
                return True
        
        elif event.type == pygame.TEXTINPUT and self.active:
            if len(self.text) < self.max_length:
                self.text = self.text[:self.cursor_pos] + event.text + self.text[self.cursor_pos:]
                self.cursor_pos += len(event.text)
            return True
        
        return False
    
    def update(self, dt: float) -> None:
        """
        Met à jour le champ de texte.
        
        Args:
            dt: Temps écoulé
        """
        # Animation du curseur
        if self.active:
            self.cursor_timer += dt
            if self.cursor_timer >= self.cursor_blink_rate:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0.0
        else:
            self.cursor_visible = False
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Dessine le champ de texte.
        
        Args:
            surface: Surface de destination
        """
        if not self.visible or not self.font:
            return
        
        # Fond
        bg_color = self.active_color if self.active else self.background_color
        bg_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        bg_surface.fill(bg_color)
        surface.blit(bg_surface, self.rect.topleft)
        
        # Bordure
        border_width = 3 if self.active else 2
        pygame.draw.rect(surface, self.border_color, self.rect, border_width)
        
        # Texte ou placeholder
        display_text = self.text if self.text else self.placeholder
        text_color = self.text_color if self.text else self.placeholder_color
        
        if display_text:
            text_surface = self.font.render(display_text, True, text_color)
            text_rect = text_surface.get_rect(
                x=self.rect.x + 5,
                centery=self.rect.centery
            )
            
            # Limiter le texte à la largeur du champ
            if text_rect.width > self.rect.width - 10:
                # Faire défiler le texte si trop long
                text_rect.x = self.rect.x + 5 - (text_rect.width - (self.rect.width - 10))
            
            surface.blit(text_surface, text_rect)
        
        # Curseur
        if self.active and self.cursor_visible and self.text:
            # Calculer la position du curseur
            cursor_text = self.text[:self.cursor_pos]
            cursor_width = self.font.size(cursor_text)[0] if cursor_text else 0
            
            cursor_x = self.rect.x + 5 + cursor_width
            cursor_y1 = self.rect.y + 5
            cursor_y2 = self.rect.bottom - 5
            
            pygame.draw.line(surface, self.text_color, (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)
    
    def get_text(self) -> str:
        """Retourne le texte actuel."""
        return self.text
    
    def set_text(self, text: str) -> None:
        """
        Définit le texte.
        
        Args:
            text: Nouveau texte
        """
        self.text = text[:self.max_length]
        self.cursor_pos = min(self.cursor_pos, len(self.text))
    
    def clear(self) -> None:
        """Vide le champ de texte."""
        self.text = ""
        self.cursor_pos = 0
    
    def set_active(self, active: bool) -> None:
        """Active ou désactive le champ."""
        self.active = active
    
    def is_active(self) -> bool:
        """Retourne si le champ est actif."""
        return self.active


class IconButton:
    """
    Bouton avec icône au lieu de texte.
    Utilisé pour l'icône des tâches et autres boutons compacts.
    """
    
    def __init__(self, x: int, y: int, size: int, icon_key: str,
                 callback: Optional[Callable[[], None]] = None, tooltip: str = ""):
        self.rect = pygame.Rect(x, y, size, size)
        self.icon_key = icon_key
        self.callback = callback
        self.tooltip = tooltip
        self.state = ButtonState.NORMAL
        self.enabled = True
        self.visible = True
        
        # Couleurs par état
        self.colors = {
            ButtonState.NORMAL: (0, 0, 0, 0),  # Transparent
            ButtonState.HOVER: UI_HOVER,
            ButtonState.PRESSED: (150, 0, 0, 200),
            ButtonState.DISABLED: (80, 80, 80, 100)
        }
        
        self.icon_surface = None
        self._load_icon()
        
        logger.debug(f"IconButton created: {icon_key} at ({x}, {y})")
    
    def _load_icon(self) -> None:
        """Charge l'icône depuis l'AssetManager."""
        try:
            self.icon_surface = asset_manager.get_image(self.icon_key)
            # Redimensionner l'icône pour qu'elle tienne dans le bouton
            icon_size = min(self.rect.width - 8, self.rect.height - 8)
            if self.icon_surface.get_width() != icon_size or self.icon_surface.get_height() != icon_size:
                self.icon_surface = pygame.transform.scale(self.icon_surface, (icon_size, icon_size))
        except Exception as e:
            logger.error(f"Failed to load icon {self.icon_key}: {e}")
            self.icon_surface = None
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Gère les événements pour ce bouton.
        
        Args:
            event: Événement pygame
            
        Returns:
            True si l'événement a été consommé
        """
        if not self.visible or not self.enabled:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            if point_in_rect(mouse_pos, self.rect):
                if self.state != ButtonState.HOVER:
                    self.state = ButtonState.HOVER
            else:
                if self.state == ButtonState.HOVER:
                    self.state = ButtonState.NORMAL
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche
                mouse_pos = pygame.mouse.get_pos()
                if point_in_rect(mouse_pos, self.rect):
                    self.state = ButtonState.PRESSED
                    return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.state == ButtonState.PRESSED:
                mouse_pos = pygame.mouse.get_pos()
                if point_in_rect(mouse_pos, self.rect):
                    self.state = ButtonState.HOVER
                    if self.callback:
                        self.callback()
                    logger.debug(f"IconButton clicked: {self.icon_key}")
                    return True
                else:
                    self.state = ButtonState.NORMAL
        
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Dessine le bouton icône.
        
        Args:
            surface: Surface sur laquelle dessiner
        """
        if not self.visible:
            return
        
        # Fond du bouton
        color = self.colors[self.state]
        if color[3] > 0:  # Si pas transparent
            button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            button_surface.fill(color)
            surface.blit(button_surface, self.rect.topleft)
        
        # Icône
        if self.icon_surface:
            icon_x = self.rect.centerx - self.icon_surface.get_width() // 2
            icon_y = self.rect.centery - self.icon_surface.get_height() // 2
            surface.blit(self.icon_surface, (icon_x, icon_y))
        
        # Bordure si hover ou pressed
        if self.state in [ButtonState.HOVER, ButtonState.PRESSED]:
            pygame.draw.rect(surface, UI_TEXT, self.rect, 2)
    
    def set_position(self, x: int, y: int) -> None:
        """Change la position du bouton."""
        self.rect.x = x
        self.rect.y = y
    
    def set_enabled(self, enabled: bool) -> None:
        """Active ou désactive le bouton."""
        self.enabled = enabled
        if not enabled:
            self.state = ButtonState.DISABLED
        else:
            self.state = ButtonState.NORMAL


class Panel:
    """
    Panneau flottant avec fond semi-transparent.
    Utilisé pour le panneau des tâches et autres overlays.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, title: str = ""):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.visible = False
        self.draggable = False
        
        # Style
        self.background_color = UI_PANEL
        self.border_color = UI_TEXT
        self.title_color = UI_TEXT
        self.border_width = 2
        
        # Contenu
        self.content_rect = pygame.Rect(
            x + 10, y + (30 if title else 10),
            width - 20, height - (40 if title else 20)
        )
        
        self.font = None
        self._load_font()
        
        logger.debug(f"Panel created: '{title}' at ({x}, {y}) size {width}x{height}")
    
    def _load_font(self) -> None:
        """Charge la police pour le titre."""
        try:
            self.font = asset_manager.get_font("ui_font")
        except Exception as e:
            logger.error(f"Failed to load panel font: {e}")
            self.font = pygame.font.SysFont(None, 18)
    
    def show(self) -> None:
        """Affiche le panneau."""
        self.visible = True
        logger.debug(f"Panel shown: '{self.title}'")
    
    def hide(self) -> None:
        """Cache le panneau."""
        self.visible = False
        logger.debug(f"Panel hidden: '{self.title}'")
    
    def toggle(self) -> None:
        """Alterne la visibilité du panneau."""
        if self.visible:
            self.hide()
        else:
            self.show()
    
    def is_visible(self) -> bool:
        """Retourne True si le panneau est visible."""
        return self.visible
    
    def contains_point(self, point: Tuple[int, int]) -> bool:
        """Vérifie si un point est dans le panneau."""
        return point_in_rect(point, self.rect) if self.visible else False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Gère les événements pour ce panneau.
        
        Args:
            event: Événement pygame
            
        Returns:
            True si l'événement a été consommé (bloque les interactions en dessous)
        """
        if not self.visible:
            return False
        
        # Bloquer les clics qui tombent sur le panneau
        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
            mouse_pos = pygame.mouse.get_pos()
            if self.contains_point(mouse_pos):
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Dessine le panneau de base.
        
        Args:
            surface: Surface sur laquelle dessiner
        """
        if not self.visible:
            return
        
        # Fond semi-transparent
        panel_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel_surface.fill(self.background_color)
        surface.blit(panel_surface, self.rect.topleft)
        
        # Bordure
        pygame.draw.rect(surface, self.border_color, self.rect, self.border_width)
        
        # Titre
        if self.title and self.font:
            title_surface = self.font.render(self.title, True, self.title_color)
            title_x = self.rect.x + (self.rect.width - title_surface.get_width()) // 2
            title_y = self.rect.y + 5
            surface.blit(title_surface, (title_x, title_y))
    
    def get_content_rect(self) -> pygame.Rect:
        """Retourne le rectangle de contenu (intérieur du panneau)."""
        return self.content_rect.copy()
    
    def set_position(self, x: int, y: int) -> None:
        """Change la position du panneau."""
        self.rect.x = x
        self.rect.y = y
        self.content_rect.x = x + 10
        self.content_rect.y = y + (30 if self.title else 10)
