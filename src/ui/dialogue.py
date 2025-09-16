"""
Système de dialogue pour A Day at the Office.
Gère les conversations avec les NPCs et les messages contextuels.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import pygame
from src.settings import WIDTH, HEIGHT, UI_PANEL, UI_TEXT
from src.core.assets import asset_manager
from src.core.utils import create_text_surface, load_json_safe

logger = logging.getLogger(__name__)


class DialogueState(Enum):
    """États possibles du système de dialogue."""
    HIDDEN = "hidden"
    SHOWING = "showing"
    WAITING_INPUT = "waiting_input"
    ANIMATING = "animating"


class DialogueChoice:
    """Choix de dialogue."""
    
    def __init__(self, text: str, callback: Optional[Callable[[], None]] = None,
                 condition: Optional[Callable[[], bool]] = None):
        self.text = text
        self.callback = callback
        self.condition = condition  # Condition pour afficher ce choix
    
    def is_available(self) -> bool:
        """Vérifie si ce choix est disponible."""
        return self.condition() if self.condition else True


class DialogueNode:
    """Noeud de dialogue."""
    
    def __init__(self, text: str, speaker: str = "", 
                 choices: Optional[List[DialogueChoice]] = None,
                 auto_continue: bool = False):
        self.text = text
        self.speaker = speaker
        self.choices = choices or []
        self.auto_continue = auto_continue
        self.duration = 0.0  # Pour l'auto-continue


class DialogueSystem:
    """
    Système de dialogue principal.
    """
    
    def __init__(self):
        self.state = DialogueState.HIDDEN
        self.current_node: Optional[DialogueNode] = None
        self.dialogue_queue: List[DialogueNode] = []
        
        # Interface
        self.dialogue_box_rect = pygame.Rect(50, HEIGHT - 200, WIDTH - 100, 150)
        self.text_area_rect = pygame.Rect(70, HEIGHT - 180, WIDTH - 140, 80)
        self.choices_start_y = HEIGHT - 90
        
        # Animation
        self.animation_time = 0.0
        self.text_reveal_speed = 50.0  # Caractères par seconde
        self.revealed_text = ""
        self.full_text = ""
        
        # Sélection de choix
        self.selected_choice = 0
        
        # Polices
        self.font_dialogue = None
        self.font_speaker = None
        self.font_choices = None
        
        # Données de localisation
        self.dialogue_data: Dict[str, Any] = {}
        
        logger.info("DialogueSystem initialized")
    
    def load_fonts(self) -> None:
        """Charge les polices nécessaires."""
        try:
            self.font_dialogue = asset_manager.get_font("body_font")
            self.font_speaker = asset_manager.get_font("ui_font")
            self.font_choices = asset_manager.get_font("body_font")
        except Exception as e:
            logger.error(f"Error loading dialogue fonts: {e}")
    
    def load_dialogue_data(self, file_path) -> bool:
        """
        Charge les données de dialogue depuis un fichier JSON.
        
        Args:
            file_path: Chemin vers le fichier de dialogues
            
        Returns:
            True si le chargement a réussi
        """
        try:
            self.dialogue_data = load_json_safe(file_path) or {}
            logger.info(f"Dialogue data loaded from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading dialogue data: {e}")
            return False
    
    def start_dialogue(self, dialogue_id: str, speaker_name: str = "") -> bool:
        """
        Démarre un dialogue.
        
        Args:
            dialogue_id: ID du dialogue dans les données
            speaker_name: Nom du locuteur
            
        Returns:
            True si le dialogue a commencé
        """
        if self.state != DialogueState.HIDDEN:
            logger.warning("Dialogue already active")
            return False
        
        # Récupérer les données du dialogue
        dialogue_lines = self.dialogue_data.get("dialogues", {}).get(dialogue_id, [])
        if not dialogue_lines:
            logger.warning(f"Dialogue not found: {dialogue_id}")
            return False
        
        # Convertir en noeuds de dialogue
        self.dialogue_queue.clear()
        for line in dialogue_lines:
            if isinstance(line, str):
                node = DialogueNode(line, speaker_name, auto_continue=True)
                self.dialogue_queue.append(node)
        
        # Commencer le premier noeud
        if self.dialogue_queue:
            self._show_next_node()
            return True
        
        return False
    
    def start_custom_dialogue(self, nodes: List[DialogueNode]) -> bool:
        """
        Démarre un dialogue personnalisé.
        
        Args:
            nodes: Liste des noeuds de dialogue
            
        Returns:
            True si le dialogue a commencé
        """
        if self.state != DialogueState.HIDDEN:
            return False
        
        self.dialogue_queue = nodes.copy()
        if self.dialogue_queue:
            self._show_next_node()
            return True
        
        return False
    
    def show_message(self, text: str, speaker: str = "", duration: float = 3.0) -> bool:
        """
        Affiche un message simple.
        
        Args:
            text: Texte du message
            speaker: Nom du locuteur
            duration: Durée d'affichage automatique
            
        Returns:
            True si le message a été affiché
        """
        if self.state != DialogueState.HIDDEN:
            return False
        
        node = DialogueNode(text, speaker, auto_continue=True)
        node.duration = duration
        
        self.dialogue_queue = [node]
        self._show_next_node()
        return True
    
    def _show_next_node(self) -> None:
        """Affiche le prochain noeud de dialogue."""
        if not self.dialogue_queue:
            self.close_dialogue()
            return
        
        self.current_node = self.dialogue_queue.pop(0)
        self.state = DialogueState.SHOWING
        self.animation_time = 0.0
        self.revealed_text = ""
        self.full_text = self.current_node.text
        self.selected_choice = 0
        
        logger.debug(f"Showing dialogue node: '{self.current_node.text[:30]}...'")
    
    def update(self, dt: float) -> None:
        """
        Met à jour le système de dialogue.
        
        Args:
            dt: Temps écoulé
        """
        if self.state == DialogueState.HIDDEN:
            return
        
        self.animation_time += dt
        
        if self.state == DialogueState.SHOWING:
            # Animation de révélation du texte
            chars_to_reveal = int(self.animation_time * self.text_reveal_speed)
            self.revealed_text = self.full_text[:chars_to_reveal]
            
            # Vérifier si tout le texte est révélé
            if len(self.revealed_text) >= len(self.full_text):
                if self.current_node and self.current_node.auto_continue:
                    # Auto-continue après un délai
                    if self.animation_time >= len(self.full_text) / self.text_reveal_speed + (self.current_node.duration or 2.0):
                        self._continue_dialogue()
                else:
                    # Attendre l'input du joueur
                    self.state = DialogueState.WAITING_INPUT
        
        elif self.state == DialogueState.WAITING_INPUT:
            # Rien à faire, attendre l'input
            pass
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Gère un événement pygame.
        
        Args:
            event: Événement à traiter
            
        Returns:
            True si l'événement a été consommé
        """
        if self.state == DialogueState.HIDDEN:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_e]:
                if self.state == DialogueState.SHOWING:
                    # Révéler tout le texte immédiatement
                    self.revealed_text = self.full_text
                    self.state = DialogueState.WAITING_INPUT
                elif self.state == DialogueState.WAITING_INPUT:
                    self._handle_continue_input()
                return True
            
            elif event.key == pygame.K_ESCAPE:
                self.close_dialogue()
                return True
            
            # Navigation dans les choix
            elif self.state == DialogueState.WAITING_INPUT and self.current_node and self.current_node.choices:
                if event.key == pygame.K_UP:
                    self.selected_choice = (self.selected_choice - 1) % len(self.current_node.choices)
                    return True
                elif event.key == pygame.K_DOWN:
                    self.selected_choice = (self.selected_choice + 1) % len(self.current_node.choices)
                    return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == DialogueState.SHOWING:
                # Révéler tout le texte
                self.revealed_text = self.full_text
                self.state = DialogueState.WAITING_INPUT
            elif self.state == DialogueState.WAITING_INPUT:
                # Vérifier si on clique sur un choix
                if self.current_node and self.current_node.choices:
                    choice_index = self._get_choice_at_position(event.pos)
                    if choice_index is not None:
                        self.selected_choice = choice_index
                        self._handle_continue_input()
                else:
                    self._handle_continue_input()
            return True
        
        return False
    
    def _get_choice_at_position(self, pos: tuple) -> Optional[int]:
        """
        Trouve le choix à une position donnée.
        
        Args:
            pos: Position (x, y)
            
        Returns:
            Index du choix ou None
        """
        if not self.current_node or not self.current_node.choices:
            return None
        
        y_offset = self.choices_start_y
        for i, choice in enumerate(self.current_node.choices):
            if not choice.is_available():
                continue
            
            choice_rect = pygame.Rect(70, y_offset, WIDTH - 140, 25)
            if choice_rect.collidepoint(pos):
                return i
            y_offset += 30
        
        return None
    
    def _handle_continue_input(self) -> None:
        """Gère l'input de continuation."""
        if not self.current_node:
            return
        
        if self.current_node.choices:
            # Exécuter le choix sélectionné
            available_choices = [c for c in self.current_node.choices if c.is_available()]
            if 0 <= self.selected_choice < len(available_choices):
                choice = available_choices[self.selected_choice]
                if choice.callback:
                    try:
                        choice.callback()
                    except Exception as e:
                        logger.error(f"Error in dialogue choice callback: {e}")
        
        self._continue_dialogue()
    
    def _continue_dialogue(self) -> None:
        """Continue vers le prochain noeud ou ferme le dialogue."""
        if self.dialogue_queue:
            self._show_next_node()
        else:
            self.close_dialogue()
    
    def close_dialogue(self) -> None:
        """Ferme le dialogue."""
        self.state = DialogueState.HIDDEN
        self.current_node = None
        self.dialogue_queue.clear()
        self.revealed_text = ""
        self.full_text = ""
        logger.debug("Dialogue closed")
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Dessine le système de dialogue.
        
        Args:
            surface: Surface de destination
        """
        if self.state == DialogueState.HIDDEN or not self.current_node:
            return
        
        # Fond du dialogue
        dialogue_surface = pygame.Surface((self.dialogue_box_rect.width, self.dialogue_box_rect.height), pygame.SRCALPHA)
        dialogue_surface.fill(UI_PANEL)
        surface.blit(dialogue_surface, self.dialogue_box_rect.topleft)
        
        # Bordure
        pygame.draw.rect(surface, UI_TEXT, self.dialogue_box_rect, 3)
        
        # Nom du locuteur
        if self.current_node.speaker and self.font_speaker:
            speaker_surface = self.font_speaker.render(self.current_node.speaker, True, UI_TEXT)
            surface.blit(speaker_surface, (self.text_area_rect.x, self.text_area_rect.y - 25))
        
        # Texte du dialogue
        if self.font_dialogue:
            text_surface = create_text_surface(
                self.revealed_text, 
                self.font_dialogue, 
                UI_TEXT, 
                self.text_area_rect.width
            )
            surface.blit(text_surface, self.text_area_rect.topleft)
        
        # Indicateur de continuation
        if self.state == DialogueState.WAITING_INPUT:
            if self.current_node.choices:
                # Afficher les choix
                self._draw_choices(surface)
            else:
                # Indicateur simple
                if self.font_dialogue:
                    continue_text = "Appuyez sur Espace pour continuer..."
                    continue_surface = self.font_dialogue.render(continue_text, True, (200, 200, 200))
                    continue_rect = continue_surface.get_rect(
                        right=self.dialogue_box_rect.right - 10,
                        bottom=self.dialogue_box_rect.bottom - 10
                    )
                    surface.blit(continue_surface, continue_rect)
    
    def _draw_choices(self, surface: pygame.Surface) -> None:
        """
        Dessine les choix de dialogue.
        
        Args:
            surface: Surface de destination
        """
        if not self.current_node or not self.current_node.choices or not self.font_choices:
            return
        
        y_offset = self.choices_start_y
        choice_index = 0
        
        for i, choice in enumerate(self.current_node.choices):
            if not choice.is_available():
                continue
            
            # Fond du choix
            choice_rect = pygame.Rect(70, y_offset, WIDTH - 140, 25)
            
            if choice_index == self.selected_choice:
                # Choix sélectionné
                choice_surface = pygame.Surface((choice_rect.width, choice_rect.height), pygame.SRCALPHA)
                choice_surface.fill((100, 100, 100, 100))
                surface.blit(choice_surface, choice_rect.topleft)
                pygame.draw.rect(surface, UI_TEXT, choice_rect, 2)
            
            # Texte du choix
            prefix = "► " if choice_index == self.selected_choice else "  "
            choice_text = prefix + choice.text
            
            choice_surface = self.font_choices.render(choice_text, True, UI_TEXT)
            surface.blit(choice_surface, (choice_rect.x + 5, choice_rect.y + 3))
            
            y_offset += 30
            choice_index += 1
    
    def is_active(self) -> bool:
        """Vérifie si le dialogue est actif."""
        return self.state != DialogueState.HIDDEN
    
    def skip_animation(self) -> None:
        """Passe l'animation de révélation du texte."""
        if self.state == DialogueState.SHOWING:
            self.revealed_text = self.full_text
            self.state = DialogueState.WAITING_INPUT
    
    def get_state(self) -> DialogueState:
        """Retourne l'état actuel du dialogue."""
        return self.state


def create_simple_dialogue(text: str, speaker: str = "") -> List[DialogueNode]:
    """
    Crée un dialogue simple avec un seul message.
    
    Args:
        text: Texte du message
        speaker: Nom du locuteur
        
    Returns:
        Liste contenant un seul noeud
    """
    return [DialogueNode(text, speaker, auto_continue=True)]


def create_choice_dialogue(text: str, choices: List[tuple], speaker: str = "") -> List[DialogueNode]:
    """
    Crée un dialogue avec des choix.
    
    Args:
        text: Texte de la question
        choices: Liste de tuples (texte_choix, callback)
        speaker: Nom du locuteur
        
    Returns:
        Liste contenant le noeud avec choix
    """
    dialogue_choices = []
    for choice_text, callback in choices:
        dialogue_choices.append(DialogueChoice(choice_text, callback))
    
    node = DialogueNode(text, speaker, dialogue_choices)
    return [node]


def create_conversation(lines: List[tuple], auto_continue: bool = True) -> List[DialogueNode]:
    """
    Crée une conversation multi-lignes.
    
    Args:
        lines: Liste de tuples (texte, locuteur)
        auto_continue: Si les lignes continuent automatiquement
        
    Returns:
        Liste des noeuds de dialogue
    """
    nodes = []
    for text, speaker in lines:
        node = DialogueNode(text, speaker, auto_continue=auto_continue)
        nodes.append(node)
    
    return nodes
