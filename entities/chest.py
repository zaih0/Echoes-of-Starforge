import pygame
import math
from core.settings import CHEST_SIZE, CHEST_COLOR, CHEST_OPEN_COLOR, PICKUP_RADIUS, PICKUP_WEAPON_COLOR

class Chest:
    def __init__(self, pos, item=None):
        self.pos = pygame.Vector2(pos)
        self.opened = False
        self.item = item  # weapon or None
        self.floating_pickup = None

    def rect(self):
        return pygame.Rect(int(self.pos.x - CHEST_SIZE//2),
                           int(self.pos.y - CHEST_SIZE//2),
                           CHEST_SIZE, CHEST_SIZE)

    def open(self):
        if not self.opened:
            self.opened = True
            if self.item:
                self.floating_pickup = FloatingPickup(self.pos, self.item)

    def draw(self, surface):
        color = CHEST_OPEN_COLOR if self.opened else CHEST_COLOR
        r = self.rect()
        pygame.draw.rect(surface, color, r, border_radius=4)
        pygame.draw.rect(surface, (30,30,40), r, width=2, border_radius=4)
        if self.floating_pickup:
            self.floating_pickup.draw(surface)

class FloatingPickup:
    def __init__(self, pos, item):
        self.pos = pygame.Vector2(pos)
        self.item = item
        self.active = True
        self.time = 0

    def update(self, dt):
        self.time += dt

    def draw(self, surface):
        if not self.active:
            return
        # bobbing animation using math.sin
        offset = 6 * math.sin(self.time * 3)  # bob up/down
        y = self.pos.y - 20 + offset
        pygame.draw.circle(surface, PICKUP_WEAPON_COLOR, (int(self.pos.x), int(y)), PICKUP_RADIUS)
        font = pygame.font.Font(None, 20)
        text = font.render(self.item.name, True, (255,255,255))
        surface.blit(text, (self.pos.x - text.get_width()/2, y - 18))
