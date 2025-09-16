from pathlib import Path
import os
from typing import Tuple

# === CONSTANTES EXISTANTES CONSERVÉES ===
WIDTH = 1200
HEIGHT = 600
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# === NOUVELLES CONSTANTES GAMEPLAY ===
# Titre du jeu
GAME_TITLE = "A Day at the Office"

# Configuration temporelle
START_TIME = "08:30"
END_TIME = "08:48"
GAME_SECONDS_PER_REAL_SECOND = 5.0

# Configuration du building
VISIBLE_FLOOR_RADIUS = 2
MIN_FLOOR = 90
MAX_FLOOR = 98
ELEVATOR_POSITION_X = 64

# Dimensions des entités
PLAYER_WIDTH = 48
PLAYER_HEIGHT = 72
TILE_SIZE = 48

# Configuration des assets
ASSETS_PATH = Path("assets")
ALT_ASSETS_PATH = Path("aassets")  # Dossier alternatif si présent
DATA_PATH = Path("src/data")

# Configuration de développement
DEV_MODE = os.getenv("DEV_MODE", "True").lower() == "true"
ASSET_SCALE = int(os.getenv("ASSET_SCALE", "2"))
FALLBACK_FONT_SIZE = int(os.getenv("FALLBACK_FONT_SIZE", "16"))

# Couleurs additionnelles
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Couleurs UI
UI_BACKGROUND = (0, 0, 0, 150)  # Fond semi-transparent
UI_HOVER = (200, 0, 0, 180)     # Hover rouge
UI_TEXT = WHITE
UI_PANEL = (0, 0, 0, 140)       # Panneau semi-transparent

# Configuration de la fenêtre
WINDOW_SIZE: Tuple[int, int] = (WIDTH, HEIGHT)