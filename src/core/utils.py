"""
Utilitaires généraux pour A Day at the Office.
Fonctions helper communes utilisées dans tout le projet.
"""

import logging
import math
from typing import Tuple, Optional, Any, Dict, List
import pygame
from pathlib import Path
import re

logger = logging.getLogger(__name__)


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Limite une valeur entre min et max.
    
    Args:
        value: Valeur à limiter
        min_value: Valeur minimum
        max_value: Valeur maximum
        
    Returns:
        Valeur limitée
    """
    return max(min_value, min(value, max_value))


def lerp(start: float, end: float, t: float) -> float:
    """
    Interpolation linéaire entre deux valeurs.
    
    Args:
        start: Valeur de début
        end: Valeur de fin
        t: Facteur d'interpolation (0.0 à 1.0)
        
    Returns:
        Valeur interpolée
    """
    return start + (end - start) * clamp(t, 0.0, 1.0)


def distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """
    Calcule la distance euclidienne entre deux points.
    
    Args:
        pos1: Premier point (x, y)
        pos2: Deuxième point (x, y)
        
    Returns:
        Distance entre les points
    """
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    return math.sqrt(dx * dx + dy * dy)


def normalize_vector(vector: Tuple[float, float]) -> Tuple[float, float]:
    """
    Normalise un vecteur 2D.
    
    Args:
        vector: Vecteur (x, y)
        
    Returns:
        Vecteur normalisé ou (0, 0) si vecteur nul
    """
    x, y = vector
    length = math.sqrt(x * x + y * y)
    
    if length == 0:
        return (0.0, 0.0)
    
    return (x / length, y / length)


def point_in_rect(point: Tuple[float, float], rect: pygame.Rect) -> bool:
    """
    Vérifie si un point est dans un rectangle.
    
    Args:
        point: Point (x, y)
        rect: Rectangle pygame
        
    Returns:
        True si le point est dans le rectangle
    """
    x, y = point
    return rect.left <= x <= rect.right and rect.top <= y <= rect.bottom


def rect_overlap(rect1: pygame.Rect, rect2: pygame.Rect) -> bool:
    """
    Vérifie si deux rectangles se chevauchent.
    
    Args:
        rect1: Premier rectangle
        rect2: Deuxième rectangle
        
    Returns:
        True si les rectangles se chevauchent
    """
    return rect1.colliderect(rect2)


def format_time_duration(seconds: float) -> str:
    """
    Formate une durée en secondes vers une chaîne lisible.
    
    Args:
        seconds: Durée en secondes
        
    Returns:
        Chaîne formatée (ex: "2:30", "1:05:30")
    """
    if seconds < 0:
        return "0:00"
    
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Récupère une valeur de dictionnaire avec fallback sécurisé.
    
    Args:
        dictionary: Dictionnaire source
        key: Clé à chercher
        default: Valeur par défaut
        
    Returns:
        Valeur trouvée ou valeur par défaut
    """
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default


def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Charge un fichier JSON avec gestion d'erreurs.
    
    Args:
        file_path: Chemin vers le fichier JSON
        
    Returns:
        Dictionnaire parsé ou None en cas d'erreur
    """
    try:
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
        logger.error(f"Error loading JSON {file_path}: {e}")
        return None


def parse_hhmm(time_str: str) -> Optional[tuple[int, int]]:
    """
    Parse une chaîne HH:MM en tuple (hour, minute).
    Retourne None si invalide.
    """
    try:
        if not isinstance(time_str, str):
            return None
        if not re.match(r"^\d{2}:\d{2}$", time_str):
            return None
        hour, minute = map(int, time_str.split(":"))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)
        return None
    except Exception:
        return None


def create_text_surface(text: str, font: pygame.font.Font, color: Tuple[int, int, int], 
                       max_width: Optional[int] = None) -> pygame.Surface:
    """
    Crée une surface de texte avec gestion du word wrap optionnel.
    
    Args:
        text: Texte à rendre
        font: Police à utiliser
        color: Couleur du texte (R, G, B)
        max_width: Largeur maximum (None = pas de limite)
        
    Returns:
        Surface contenant le texte rendu
    """
    if not max_width:
        # Simple rendu sans word wrap
        return font.render(text, True, color)
    
    # Word wrap basique
    words = text.split(' ')
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        test_width = font.size(test_line)[0]
        
        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    # Créer la surface finale
    if not lines:
        return pygame.Surface((0, 0))
    
    line_height = font.get_height()
    total_height = len(lines) * line_height
    surface = pygame.Surface((max_width, total_height), pygame.SRCALPHA)
    
    for i, line in enumerate(lines):
        line_surface = font.render(line, True, color)
        surface.blit(line_surface, (0, i * line_height))
    
    return surface


def draw_text_centered(surface: pygame.Surface, text: str, font: pygame.font.Font, 
                      color: Tuple[int, int, int], center_pos: Tuple[int, int]) -> None:
    """
    Dessine du texte centré sur une surface.
    
    Args:
        surface: Surface de destination
        text: Texte à dessiner
        font: Police à utiliser
        color: Couleur du texte
        center_pos: Position du centre (x, y)
    """
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center_pos)
    surface.blit(text_surface, text_rect)


def ease_in_out_cubic(t: float) -> float:
    """
    Fonction d'easing cubic in-out.
    
    Args:
        t: Valeur d'entrée (0.0 à 1.0)
        
    Returns:
        Valeur avec easing appliqué
    """
    t = clamp(t, 0.0, 1.0)
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


def screen_shake(intensity: float, duration: float, current_time: float) -> Tuple[int, int]:
    """
    Génère un offset de screen shake.
    
    Args:
        intensity: Intensité du shake (pixels)
        duration: Durée totale du shake
        current_time: Temps actuel dans le shake
        
    Returns:
        Offset (x, y) à appliquer
    """
    if current_time >= duration:
        return (0, 0)
    
    # Diminuer l'intensité au fil du temps
    progress = current_time / duration
    current_intensity = intensity * (1.0 - progress)
    
    # Génération pseudo-aléatoire basée sur le temps
    import random
    random.seed(int(current_time * 100))
    
    offset_x = random.randint(-int(current_intensity), int(current_intensity))
    offset_y = random.randint(-int(current_intensity), int(current_intensity))
    
    return (offset_x, offset_y)


def color_lerp(color1: Tuple[int, int, int], color2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    """
    Interpolation linéaire entre deux couleurs.
    
    Args:
        color1: Couleur de début (R, G, B)
        color2: Couleur de fin (R, G, B)
        t: Facteur d'interpolation (0.0 à 1.0)
        
    Returns:
        Couleur interpolée (R, G, B)
    """
    t = clamp(t, 0.0, 1.0)
    
    r = int(lerp(color1[0], color2[0], t))
    g = int(lerp(color1[1], color2[1], t))
    b = int(lerp(color1[2], color2[2], t))
    
    return (clamp(r, 0, 255), clamp(g, 0, 255), clamp(b, 0, 255))


def get_floor_number_from_key(key_action: str) -> Optional[int]:
    """
    Convertit une action de touche chiffre en numéro d'étage.
    
    Args:
        key_action: Action de la forme "floor_X"
        
    Returns:
        Numéro d'étage (90-99) ou None
    """
    if not key_action.startswith("floor_"):
        return None
    
    try:
        digit = int(key_action.split("_")[1])
        return 90 + digit
    except (IndexError, ValueError):
        return None


def create_gradient_surface(width: int, height: int, 
                           color1: Tuple[int, int, int], 
                           color2: Tuple[int, int, int],
                           vertical: bool = True) -> pygame.Surface:
    """
    Crée une surface avec un dégradé de couleur.
    
    Args:
        width: Largeur de la surface
        height: Hauteur de la surface
        color1: Couleur de début
        color2: Couleur de fin
        vertical: True pour dégradé vertical, False pour horizontal
        
    Returns:
        Surface avec dégradé
    """
    surface = pygame.Surface((width, height))
    
    if vertical:
        for y in range(height):
            t = y / height if height > 0 else 0
            color = color_lerp(color1, color2, t)
            pygame.draw.line(surface, color, (0, y), (width, y))
    else:
        for x in range(width):
            t = x / width if width > 0 else 0
            color = color_lerp(color1, color2, t)
            pygame.draw.line(surface, color, (x, 0), (x, height))
    
    return surface


def log_performance(func_name: str, start_time: float, end_time: float, threshold: float = 0.016) -> None:
    """
    Log les performances d'une fonction si elle dépasse le seuil.
    
    Args:
        func_name: Nom de la fonction
        start_time: Temps de début (pygame.time.get_ticks())
        end_time: Temps de fin
        threshold: Seuil en secondes (défaut: 16ms pour 60 FPS)
    """
    duration = (end_time - start_time) / 1000.0  # Convertir en secondes
    
    if duration > threshold:
        logger.warning(f"Performance: {func_name} took {duration:.4f}s (threshold: {threshold:.4f}s)")
    elif duration > threshold / 2:
        logger.debug(f"Performance: {func_name} took {duration:.4f}s")
