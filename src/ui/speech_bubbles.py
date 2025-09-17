import logging
import random
import time
from typing import Dict, List, Optional, Tuple, Union
import pygame
from src.core.assets import asset_manager

logger = logging.getLogger(__name__)

def _safe_font(size: int) -> pygame.font.Font:
    try:
        return pygame.font.Font("assets/fonts/Pixellari.ttf", size)
    except Exception:
        try:
            return asset_manager.get_font("body_font")
        except Exception:
            return pygame.font.SysFont("Arial", size, bold=True)

def _get_screen_bounds(default_w: int = 800) -> int:
    surf = pygame.display.get_surface()
    return surf.get_width() if surf else default_w

class SpeechBubble:
    """
    Bulle de dialogue avec wrap, pagination (list[str]) et durée auto.
    - text_or_list: str ou List[str]
    """
    def __init__(
        self,
        text_or_list: Union[str, List[str]],
        npc_reference=None,
        duration: Optional[float] = None,
        color: Tuple[int, int, int] = (255, 255, 255),
        max_width: Optional[int] = None,
        font_size: int = 18,
        cps: int = 16,           # characters per second pour durée auto
        min_duration: float = 2.0,
        max_duration: float = 8.0,
    ):
        self.color = color
        self.npc_reference = npc_reference
        self.font = _safe_font(font_size)
        self.alpha = 255
        self.segment_index = 0
        self.cps = cps
        self.min_duration = min_duration
        self.max_duration = max_duration

        # normalise en liste de segments
        if isinstance(text_or_list, str):
            self.segments: List[str] = [text_or_list]
        else:
            self.segments = [str(s) for s in text_or_list] if text_or_list else [""]

        # largeur max dynamique (60% de l’écran, min 250, max 520)
        screen_w = _get_screen_bounds()
        self.max_width = max_width or max(250, min(int(screen_w * 0.6), 520))

        # états
        self.start_time = time.time()
        self.segment_start_time = self.start_time
        self.duration = duration  # si None => auto
        self.bubble_surface = None
        self.x = 0
        self.y = 0

        # construit la première bulle
        self._create_bubble(self.segments[self.segment_index])

    # ---------- mise en forme & rendu ----------
    def _wrap_text(self, text: str) -> List[str]:
        """
        Wrap robuste qui respecte les \n explicites.
        Coupe les mots surlongs si nécessaire.
        """
        max_w = self.max_width - 30  # padding intérieur
        lines: List[str] = []
        for raw_line in text.replace("\r\n", "\n").split("\n"):
            words = raw_line.split(" ")
            if not words:
                lines.append("")
                continue

            current: List[str] = []
            for w in words:
                # si mot trop long, on le “hyphenate” grossièrement
                if self.font.size(w)[0] > max_w:
                    # vide la ligne en cours si pas vide
                    if current:
                        lines.append(" ".join(current))
                        current = []
                    # coupe le mot en morceaux
                    chunk = ""
                    for ch in w:
                        if self.font.size(chunk + ch)[0] <= max_w:
                            chunk += ch
                        else:
                            # pousse le chunk courant
                            if chunk:
                                lines.append(chunk + "-")
                            chunk = ch
                    if chunk:
                        current = [chunk]  # nouveau début de ligne
                else:
                    test_line = (" ".join(current + [w])).strip()
                    if self.font.size(test_line)[0] <= max_w:
                        current.append(w)
                    else:
                        lines.append(" ".join(current))
                        current = [w]
            if current:
                lines.append(" ".join(current))
            # préserver les lignes vides entre paragraphes
        return lines if lines else [""]

    def _auto_duration_for(self, text: str) -> float:
        if self.duration is not None:
            return float(self.duration)
        # base sur caractères + un bonus par ligne
        n_chars = len(text)
        est = n_chars / max(1, self.cps)
        lines = max(1, len(self._wrap_text(text)))
        est += 0.4 * lines
        return max(self.min_duration, min(est, self.max_duration))

    def _create_bubble(self, text: str):
        lines = self._wrap_text(text)

        line_height = self.font.get_height() + 2
        text_height = len(lines) * line_height
        text_width = max((self.font.size(l)[0] for l in lines), default=0)

        bubble_w = text_width + 30  # padding L/R 15
        bubble_h = text_height + 25 # padding T/B 12

        self.bubble_surface = pygame.Surface((bubble_w, bubble_h + 15), pygame.SRCALPHA)

        # Ombre
        shadow_rect = pygame.Rect(2, 2, bubble_w, bubble_h)
        pygame.draw.rect(self.bubble_surface, (0, 0, 0, 100), shadow_rect, border_radius=12)

        # Fond + contour
        main_rect = pygame.Rect(0, 0, bubble_w, bubble_h)
        pygame.draw.rect(self.bubble_surface, (0, 0, 0, 200), main_rect, border_radius=12)
        pygame.draw.rect(self.bubble_surface, self.color, main_rect, width=3, border_radius=12)

        # Queue
        tail = [
            (bubble_w // 2 - 8, bubble_h),
            (bubble_w // 2, bubble_h + 12),
            (bubble_w // 2 + 8, bubble_h)
        ]
        pygame.draw.polygon(self.bubble_surface, (0, 0, 0, 200), tail)
        pygame.draw.polygon(self.bubble_surface, self.color, tail, width=3)

        # Texte centré
        for i, line in enumerate(lines):
            surf = self.font.render(line, True, self.color)
            tx = (bubble_w - surf.get_width()) // 2
            ty = 12 + i * line_height
            self.bubble_surface.blit(surf, (tx, ty))

        # reset timer de segment avec durée auto
        self.segment_duration = self._auto_duration_for(text)
        self.segment_start_time = time.time()
        self.alpha = 255

    # ---------- cycle de vie ----------
    def _advance_segment(self) -> bool:
        """Passe au segment suivant. Retourne False si plus de segments."""
        self.segment_index += 1
        if self.segment_index >= len(self.segments):
            return False
        self._create_bubble(self.segments[self.segment_index])
        return True

    def update(self, dt: float) -> bool:
        # suit le NPC avec ancres écran
        if self.npc_reference and self.bubble_surface:
            bw = self.bubble_surface.get_width()
            bh = self.bubble_surface.get_height()
            if hasattr(self.npc_reference, "_bubble_anchor_x") and hasattr(self.npc_reference, "_bubble_anchor_y"):
                self.x = int(self.npc_reference._bubble_anchor_x - bw // 2)
                self.y = int(self.npc_reference._bubble_anchor_y - bh - 6)
            elif hasattr(self.npc_reference, "x") and hasattr(self.npc_reference, "y"):
                self.x = int(self.npc_reference.x - bw // 2)
                self.y = int(self.npc_reference.y - 80)

        elapsed_segment = time.time() - self.segment_start_time

        # fade out dans les 0.5 dernières secondes du segment
        if elapsed_segment > self.segment_duration - 0.5:
            fade = (elapsed_segment - (self.segment_duration - 0.5)) / 0.5
            self.alpha = max(0, int(255 * (1.0 - fade)))
        else:
            self.alpha = 255

        # fin du segment -> avancer ou terminer
        if elapsed_segment >= self.segment_duration:
            if not self._advance_segment():
                return False  # plus de segments -> supprimer la bulle

        return True

    def draw(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        if not self.bubble_surface:
            return
        if self.alpha < 255:
            s = self.bubble_surface.copy()
            s.set_alpha(self.alpha)
            screen.blit(s, (self.x + offset_x, self.y + offset_y))
        else:
            screen.blit(self.bubble_surface, (self.x + offset_x, self.y + offset_y))


class SpeechBubbleManager:
    def __init__(self):
        self.bubbles: List[SpeechBubble] = []
        self.random_phrases = [
            "Il fait beau aujourd'hui !",
            "Tu as vu le nouveau projet ?",
            "Le café est vraiment bon ce matin.",
            "J'ai hâte d'être en week-end.",
            "Cette réunion était interminable...",
            "Tu as fini tes rapports ?",
            "On devrait déjeuner ensemble !",
            "L'imprimante est encore en panne ?",
            "Bon courage pour la présentation !",
            "Comment ça va aujourd'hui ?",
        ]
        self.last_random_time = 0.0
        self.random_interval = 15.0
        self._delayed: Optional[Tuple[float, str, object, Tuple[int,int,int]]] = None
        logger.info("SpeechBubbleManager initialized")

    def add_bubble(
        self,
        text_or_list: Union[str, List[str]],
        npc_reference=None,
        duration: Optional[float] = None,
        color: Tuple[int, int, int] = (255, 255, 255),
    ):
        # Éliminer l'ancienne bulle du même NPC avant d'ajouter la nouvelle
        if npc_reference is not None:
            self.bubbles = [b for b in self.bubbles if b.npc_reference is not npc_reference]
        
        bubble = SpeechBubble(text_or_list, npc_reference, duration, color)
        self.bubbles.append(bubble)
        sample = text_or_list[0] if isinstance(text_or_list, list) and text_or_list else text_or_list
        logger.debug(f"Speech bubble added: {str(sample)[:40]}...")

    def add_random_conversation(self, npcs: List, current_time: float):
        if current_time - self.last_random_time < self.random_interval:
            return
        if len(npcs) < 2:
            return

        npc1, npc2 = random.sample(npcs, 2)

        if hasattr(npc1, 'current_floor') and hasattr(npc2, 'current_floor'):
            if npc1.current_floor != npc2.current_floor:
                return
            # Vérifie qu'ils sont proches horizontalement
            try:
                dist = abs(int(npc1.x) - int(npc2.x))
            except Exception:
                dist = 9999
            if dist > 200:
                return

        # Déclenche une petite conversation
        phrase = random.choice(self.random_phrases)
        self.add_bubble(phrase, npc1, color=(200, 200, 255))

        # 30% de chances d'une réponse un peu plus tard
        if random.random() < 0.3:
            responses = ["Ah oui !", "Exactement !", "Je vois...", "Intéressant !", "Bien sûr !", "C'est vrai !"]
            resp = random.choice(responses)
            # on programme l'affichage dans ~1.5s
            self._delayed = (time.time() + 1.5, resp, npc2, (255, 200, 200))

        self.last_random_time = current_time

    # --- helpers de haut niveau ---
    def say(self, text_or_list: Union[str, List[str]], npc_reference=None,
            duration: Optional[float] = None, color: Tuple[int, int, int] = (255, 255, 255)):
        """Alias clair de add_bubble."""
        self.add_bubble(text_or_list, npc_reference, duration, color)

    def speak_from_dict(self, loc: Dict, key_path: List[str], npc_reference=None,
                        duration: Optional[float] = None, color: Tuple[int, int, int] = (255, 255, 255)):
        """
        Récupère proprement une clé de ton JSON (ex: key_path=['dialogues','boss_morning'])
        et crée la/les bulles correspondantes. Accepte str ou List[str] dans le JSON.
        """
        try:
            node = loc
            for k in key_path:
                node = node[k]
        except Exception:
            logger.warning(f"Clé introuvable dans le JSON: {'/'.join(key_path)}")
            return
        self.add_bubble(node, npc_reference, duration, color)

    # --- cycle de vie global ---
    def _handle_delayed_if_needed(self):
        if self._delayed:
            when, text, npc, color = self._delayed
            if time.time() >= when:
                self.add_bubble(text, npc, None, color)
                self._delayed = None

    def update(self, dt: float):
        """Met à jour bulles + réponses retardées et supprime celles expirées."""
        # réponses planifiées
        self._handle_delayed_if_needed()

        # met à jour chaque bulle et garde celles encore actives
        alive: List[SpeechBubble] = []
        for b in self.bubbles:
            # clamp à l'écran (évite que la bulle soit coupée hors-écran)
            if b.bubble_surface:
                screen_w = _get_screen_bounds()
                bw = b.bubble_surface.get_width()
                # si pas d'ancre NPC, b.x/y restent ce qu'ils sont (tu peux les setter à la création)
                b.x = max(8, min(b.x, screen_w - bw - 8))
            if b.update(dt):
                alive.append(b)
        self.bubbles = alive

    def draw(self, screen: pygame.Surface):
        for b in self.bubbles:
            b.draw(screen)

    def clear(self):
        self.bubbles.clear()
        self._delayed = None

