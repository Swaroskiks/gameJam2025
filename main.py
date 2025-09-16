import pygame
import sys
from src.settings import WIDTH, HEIGHT, FPS, BLACK, WHITE

def main():
    pygame.init()
    pygame.display.set_caption("GameJam 2025")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BLACK)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()