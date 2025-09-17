import pygame
import sys
from src.settings import WIDTH, HEIGHT, FPS, WHITE

def draw_center(surface, text, font, color, y):
    ts = font.render(text, True, color)
    tr = ts.get_rect(center=(WIDTH // 2, y))  # ✅ milieu exact de l'écran
    surface.blit(ts, tr)

def credits_loop(screen, clock):
    bg = pygame.image.load("assets/images/wtc.png").convert()
    bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))

    font_title = pygame.font.Font("assets/fonts/Pixellari.ttf", 36)
    font_h2    = pygame.font.Font("assets/fonts/Pixellari.ttf", 28)
    font_body  = pygame.font.Font("assets/fonts/Pixellari.ttf", 18)
    font_btn   = pygame.font.Font("assets/fonts/Pixellari.ttf", 28)

    lines = [
        ("CRÉDITS", "title"),
        ("Équipe", "h2"),
        ("Mouad M. - Loic D. - Tom W. - Auguste S. - Yohan L.", "body"),
        ("", "sp"),
        ("Tech & Outils", "h2"),
        ("Python 3.12, Pygame 2.6", "body"),
        ("VS Code, Git/GitHub", "body"),
        ("Pixellari.ttf (thanks to the creator)", "body"),
        ("", "sp"),
        ("Musique & SFX", "h2"),
        ("Ambiances originales (placeholder)", "body"),
        ("", "sp"),
        ("Remerciements", "h2"),
        ("ESIEE / Friends / Playtesters", "body"),
        ("La communauté Pygame ", "body"),
        ("© 2025 Office day - GameJam Edition", "body"),
    ]

    # Bouton Retour
    btn_w, btn_h = 220, 64
    btn_rect = pygame.Rect((WIDTH - btn_w) // 2, HEIGHT - btn_h - 40, btn_w, btn_h)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "back"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_rect.collidepoint(event.pos):
                    return "back"

        # Fond
        screen.blit(bg, (0, 0))

        # Panneau semi-transparent
        panel_margin_x = 120
        panel_margin_y = 40
        panel = pygame.Surface((WIDTH - 2 * panel_margin_x, HEIGHT - 2 * panel_margin_y - 100), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        screen.blit(panel, (panel_margin_x, panel_margin_y))
        
        # Texte
        y = panel_margin_y + 40
        line_gap = 26   # moins d'espace entre les lignes de body
        for text, kind in lines:
            if kind == "sp":
                y += 4   # petit saut de ligne
                continue
            if kind == "title":
                draw_center(screen, text, font_title, WHITE, y)
                y += 35   # au lieu de 64
            elif kind == "h2":
                draw_center(screen, text, font_h2, WHITE, y)
                y += 28   # au lieu de 48
            else:
                draw_center(screen, text, font_body, WHITE, y)
                y += line_gap

        # Bouton Retour (semi-transparent + hover)
        mouse_pos = pygame.mouse.get_pos()
        btn_surface = pygame.Surface((btn_rect.width, btn_rect.height), pygame.SRCALPHA)
        if btn_rect.collidepoint(mouse_pos):
            btn_surface.fill((200, 0, 0, 180))
        else:
            btn_surface.fill((0, 0, 0, 150))
        screen.blit(btn_surface, btn_rect.topleft)

        btn_text = font_btn.render("Retour", True, WHITE)
        btn_text_rect = btn_text.get_rect(center=btn_rect.center)
        screen.blit(btn_text, btn_text_rect)

        pygame.display.flip()
        clock.tick(FPS)