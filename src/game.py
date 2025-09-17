import pygame
from src.settings import WIDTH, HEIGHT, FPS, BLACK, WHITE

def game_loop(screen, clock):
    player = pygame.Rect(WIDTH - 20, HEIGHT - 20, 40, 40)
    speed = 10
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])

        player.x += speed * dx
        player.y += speed * dy
        player.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, player, border_radius=6)
        pygame.display.flip()
        clock.tick(FPS)