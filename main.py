import pygame
import sys
from src.settings import WIDTH, HEIGHT, FPS
from src.menu import menu_loop
from src.game import game_loop
from src.credits import credits_loop   # ⬅️ ajout

def main():
    pygame.init()
    pygame.display.set_caption("The Horse")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    while True:
        choice = menu_loop(screen, clock)

        if choice == "jouer":
            game_loop(screen, clock)
        elif choice in ("crédits", "credits"):
            credits_loop(screen, clock)   # ⬅️ ouvre la page crédits, ESC/Retour → menu
        elif choice in ("options",):
            pass
        elif choice in ("quit", "quitter"):
            break

        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()