# entities/chest.py
import pygame
import math
from core.settings import (
    CHEST_SIZE,
    CHEST_COLOR,
    CHEST_OPEN_COLOR,
    PICKUP_RADIUS,
    PICKUP_WEAPON_COLOR,
    PICKUP_CHARM_COLOR
)

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

    def draw_at_position(self, screen, screen_pos):
        """Draw chest at specific screen position"""
        x, y = screen_pos
        rect = pygame.Rect(
            int(x - CHEST_SIZE // 2),
            int(y - CHEST_SIZE // 2),
            CHEST_SIZE,
            CHEST_SIZE
        )

        color = CHEST_OPEN_COLOR if self.opened else CHEST_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=4)
        pygame.draw.rect(screen, (20, 20, 30), rect, 2, border_radius=4)

        if self.pickup and self.pickup.active:
            self.pickup.draw_at_position(screen, screen_pos)


class FloatingPickup:
    def __init__(self, pos, item):
        self.base_pos = pygame.Vector2(pos)
        self.pos = pygame.Vector2(pos)
        self.item = item
        self.active = True
        self.timer = 0

    def update(self, dt):
        if not self.active:
            return
        self.timer += dt

        # Bobbing animation
        bob = math.sin(self.timer * 3.5) * 6
        self.pos.y = self.base_pos.y - 24 + bob

    def draw_at_position(self, screen, screen_pos):
        if not self.active:
            return

        x, y = screen_pos
        
        # Color by item type
        if getattr(self.item, "type", "") == "charm":
            color = PICKUP_CHARM_COLOR
        else:
            color = PICKUP_WEAPON_COLOR

        # Adjust for bobbing animation
        draw_y = y - 24 + math.sin(self.timer * 3.5) * 6
        
        pygame.draw.circle(
            screen,
            color,
            (int(x), int(draw_y)),
            PICKUP_RADIUS
        )

        # Item name
        font = pygame.font.Font(None, 18)
        text = font.render(self.item.name, True, (255, 255, 255))
        screen.blit(
            text,
            (x - text.get_width() // 2, draw_y - 20)
        )