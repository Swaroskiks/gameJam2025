from __future__ import annotations

import sys
import pygame as pg

import settings as S


def initialize_pygame():
    pg.init()
    pg.display.set_caption(S.TITLE)
    screen = pg.display.set_mode(S.screen_size())
    clock = pg.time.Clock()
    font = pg.font.Font(None, 20)
    return screen, clock, font


def handle_events():
    for event in pg.event.get():
        if event.type == pg.QUIT:
            return False
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            return False
    return True


def draw_hud(screen: pg.Surface, clock: pg.time.Clock, font: pg.font.Font) -> None:
    fps_text = font.render(f"FPS: {clock.get_fps():.0f}", True, S.TEXT_COLOR)
    screen.blit(fps_text, (8, 8))


def main():
    screen, clock, font = initialize_pygame()

    running = True
    while running:
        dt_seconds = clock.tick(S.FPS) / 1000.0 

        running = handle_events()

        screen.fill(S.BACKGROUND_COLOR)
        draw_hud(screen, clock, font)
        pg.display.flip()

    pg.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()


