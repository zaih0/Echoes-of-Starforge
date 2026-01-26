import pygame, math
from core.settings import *

class FloatingPickup:
    def __init__(self, pos, item):
        self.pos = pygame.Vector2(pos)
        self.item = item
        self.time = 0
        self.active = True

    def update(self, dt):
        self.time += dt

    def draw(self, screen):
        if not self.active: return
        y = int(self.pos.y - 20 + math.sin(self.time*3)*6)
        pygame.draw.circle(screen, (140,220,255), (int(self.pos.x), y), PICKUP_RADIUS)
        font = pygame.font.Font(None, 20)
        text = font.render(self.item.name, True, (255,255,255))
        screen.blit(text, (self.pos.x - text.get_width()/2, y - 18))

class Chest:
    def __init__(self, pos, item):
        self.pos = pygame.Vector2(pos)
        self.item = item
        self.opened = False
        self.pickup = None

    def open(self):
        if not self.opened:
            self.opened = True
            self.pickup = FloatingPickup(self.pos, self.item)

    def draw(self, screen):
        color = (120,100,70) if self.opened else (190,150,90)
        pygame.draw.rect(screen, color, (self.pos.x-11, self.pos.y-11, 22, 22))
        if self.pickup:
            self.pickup.draw(screen)
