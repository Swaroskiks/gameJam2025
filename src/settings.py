WINDOW_WIDTH: int = 1280
WINDOW_HEIGHT: int = 720
TITLE: str = "GameJam 2025 - Destrier"

FPS: int = 60

BACKGROUND_COLOR: tuple[int, int, int] = (20, 20, 24)
TEXT_COLOR: tuple[int, int, int] = (200, 200, 200)


def screen_size() -> tuple[int, int]:
    """Return the default screen size as a tuple.

    Using a helper avoids duplicating the width/height tuple everywhere.
    """
    return (WINDOW_WIDTH, WINDOW_HEIGHT)


