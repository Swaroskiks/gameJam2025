import pygame
from pygame.surface import Surface
from typing import Tuple
from settings import WIDTH, FLOORS_Y, ELEVATOR_X, ELEVATOR_WIDTH

class Player:
    def __init__(self, pos: Tuple[int, int], speed: int = 5, width: int = 48, height: int = 96, floor_index: int = 0):
        self.x, self.y = pos
        self.speed = speed
        self.width = width
        self.height = height
        self.color = (50, 120, 200)  # Couleur temporaire
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.floors = FLOORS_Y
        self.nb_floors = len(self.floors)
        self.floor_index = floor_index
        self.elevator_x = ELEVATOR_X
        self.elevator_width = ELEVATOR_WIDTH
        self.set_y_from_floor()
        # Pour éviter le spam de changement d'étage
        self.floor_change_pressed = {"up": False, "down": False}

    def set_y_from_floor(self):
        self.y = self.floors[self.floor_index] - self.height
        self.rect.y = self.y

    def in_elevator(self):
        # Le joueur doit être entièrement dans la zone ascenseur
        return self.elevator_x <= self.x <= self.elevator_x + self.elevator_width - self.width

    def handle_input(self, keys):
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.x += self.speed
        # Changement d'étage uniquement si le joueur est dans l'ascenseur
        if self.in_elevator():
            # Flèche haut
            if keys[pygame.K_UP]:
                if not self.floor_change_pressed["up"] and self.floor_index < self.nb_floors - 1:
                    self.floor_index += 1
                    self.set_y_from_floor()
                self.floor_change_pressed["up"] = True
            else:
                self.floor_change_pressed["up"] = False
            # Flèche bas
            if keys[pygame.K_DOWN]:
                if not self.floor_change_pressed["down"] and self.floor_index > 0:
                    self.floor_index -= 1
                    self.set_y_from_floor()
                self.floor_change_pressed["down"] = True
            else:
                self.floor_change_pressed["down"] = False
        else:
            # Si on sort de l'ascenseur, on réinitialise
            self.floor_change_pressed["up"] = False
            self.floor_change_pressed["down"] = False
        self.rect.x = self.x

    def update(self):
        # Limiter le joueur à l'écran
        self.x = max(0, min(self.x, WIDTH - self.width))
        self.rect.x = self.x
        # Ne pas rappeler set_y_from_floor ici, sinon le joueur "vole" à chaque frame
        self.rect.y = self.y

    def draw(self, surface: Surface):
        pygame.draw.rect(surface, self.color, self.rect)
