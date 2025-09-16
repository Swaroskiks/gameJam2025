import pygame
import sys
from src.settings import WIDTH, HEIGHT, FPS, BLACK, WHITE

def main():
    pygame.init()
    pygame.display.set_caption("The Horse")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    
    background = pygame.image.load("assets/images/background.png").convert()
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.blit(background, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)


    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()