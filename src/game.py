import pygame
import sys
from settings import WIDTH, HEIGHT, FPS, PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_SPEED, FLOORS_Y, ELEVATOR_X, ELEVATOR_WIDTH
from characters.player import Player

FLOORS = FLOORS_Y
ELEVATOR_COLOR = (180, 180, 180)

def draw_floors(surface):
    for y in FLOORS:
        pygame.draw.rect(surface, ELEVATOR_COLOR, (ELEVATOR_X, y - 4, ELEVATOR_WIDTH, 8))
        pygame.draw.line(surface, (80, 80, 80), (0, y), (WIDTH, y), 4)

def run_game():
    pygame.init()
    pygame.display.set_caption("The Horse")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    try:
        background = pygame.image.load("assets/images/background.png").convert()
        background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    except Exception:
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill((200, 200, 255))
    player = Player(
        pos=(WIDTH // 2 - PLAYER_WIDTH // 2, FLOORS[0] - PLAYER_HEIGHT),
        speed=PLAYER_SPEED,
        width=PLAYER_WIDTH,
        height=PLAYER_HEIGHT,
        floor_index=0
    )
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        keys = pygame.key.get_pressed()
        player.handle_input(keys)
        player.update()
        screen.blit(background, (0, 0))
        draw_floors(screen)
        player.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()

