import pygame
import sys
from src.settings import WIDTH, HEIGHT, FPS, WHITE

def draw_text(surface, text, font, color, rect):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)

def menu_loop(screen, clock):
    font = pygame.font.Font("assets/fonts/Pixellari.ttf", 60)

    button_texts = ["Jouer", "Options", "Crédits", "Quitter"]
    buttons = []
    button_width, button_height = 300, 80
    spacing = 20
    total_height = len(button_texts) * button_height + (len(button_texts)-1) * spacing
    start_y = (HEIGHT - total_height) // 2

    for i, text in enumerate(button_texts):
        rect = pygame.Rect(
            (WIDTH - button_width) // 2,
            start_y + i * (button_height + spacing),
            button_width,
            button_height
        )
        buttons.append((rect, text))

    background = pygame.image.load("assets/images/background_.jpg").convert()
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()   # ✅ ferme direct la fenêtre
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, text in buttons:
                    if rect.collidepoint(event.pos):
                        if text.lower() == "quitter":  # ✅ ferme direct si bouton Quitter
                            pygame.quit()
                            sys.exit()
                        return text.lower()

        screen.blit(background, (0, 0))

        mouse_pos = pygame.mouse.get_pos()
        for rect, text in buttons:
            button_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            if rect.collidepoint(mouse_pos):
                button_surface.fill((200, 0, 0, 180))  # rouge semi-transparent
            else:
                button_surface.fill((0, 0, 0, 150))    # noir semi-transparent
            screen.blit(button_surface, rect.topleft)
            draw_text(screen, text, font, WHITE, rect)

        pygame.display.flip()
        clock.tick(FPS)