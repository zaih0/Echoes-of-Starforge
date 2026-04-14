# entities/chest.py
import pygame
import math
from core.settings import (
    CHEST_SIZE,
    CHEST_COLOR,
    CHEST_OPEN_COLOR,
    PICKUP_RADIUS,
    PICKUP_WEAPON_COLOR,
    PICKUP_CHARM_COLOR,
    OPEN_RANGE
)

class Chest:
    def __init__(self, pos, item):
        self.pos = pygame.Vector2(pos)
        self.item = item
        self.opened = False
        self.pickup = None
        self.open_cooldown = 0  # Prevent rapid opening/closing
    
    def can_open(self, player_pos):
        """Check if player is close enough to open"""
        if self.opened:
            return False
        distance = (player_pos - self.pos).length()
        return distance < OPEN_RANGE
    
    def open(self, player):
        """Open chest and create pickup"""
        if not self.opened and self.open_cooldown <= 0:
            self.opened = True
            self.pickup = FloatingPickup(self.pos.copy(), self.item)
            self.open_cooldown = 0.5  # Half second cooldown
            return True
        return False
    
    def update(self, player, dt, keys):
        """Update chest state"""
        if self.open_cooldown > 0:
            self.open_cooldown -= dt

        # Open chest when player presses E nearby
        if player and not self.opened and self.can_open(player.pos):
            if keys[pygame.K_e]:
                self.open(player)

        if self.pickup:
            self.pickup.update(dt)
    
    def draw_at_position(self, screen, screen_pos):
        """Draw chest at specific screen position"""
        x, y = screen_pos.x, screen_pos.y
        
        # Draw larger hitbox area (visual only for debugging)
        # pygame.draw.circle(screen, (255, 255, 255, 50), (int(x), int(y)), OPEN_RANGE, 1)
        
        # Draw chest
        rect = pygame.Rect(
            int(x - CHEST_SIZE // 2),
            int(y - CHEST_SIZE // 2),
            CHEST_SIZE,
            CHEST_SIZE
        )

        color = CHEST_OPEN_COLOR if self.opened else CHEST_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=4)
        pygame.draw.rect(screen, (20, 20, 30), rect, 2, border_radius=4)
        
        # Draw chest lid
        if not self.opened:
            lid_rect = pygame.Rect(
                rect.x + 4,
                rect.y + 4,
                rect.width - 8,
                8
            )
            pygame.draw.rect(screen, (200, 170, 130), lid_rect, border_radius=2)
        
        # Draw key hint if not opened
        if not self.opened:
            font = pygame.font.Font(None, 24)
            text = font.render("Press E", True, (255, 255, 200))
            text_rect = text.get_rect(center=(x, y - 40))
            screen.blit(text, text_rect)

        if self.pickup and self.pickup.active:
            self.pickup.draw_at_position(screen, (x, y))


class FloatingPickup:
    def __init__(self, pos, item):
        self.base_pos = pygame.Vector2(pos)
        self.pos = pygame.Vector2(pos)
        self.item = item
        self.active = True
        self.timer = 0
        self.collected = False
        self.collect_delay = 0.3  # Delay before can be collected
    
    def update(self, dt):
        if not self.active or self.collected:
            return
        
        self.timer += dt
        
        # Update collect delay
        if self.collect_delay > 0:
            self.collect_delay -= dt
        
        # Bobbing animation
        bob = math.sin(self.timer * 3.5) * 8  # Increased bobbing height
        self.pos.y = self.base_pos.y - 30 + bob  # Start higher
    
    def can_be_collected(self):
        """Check if pickup can be collected"""
        return self.collect_delay <= 0 and not self.collected
    
    def collect(self):
        """Mark pickup as collected"""
        if self.can_be_collected():
            self.collected = True
            self.active = False
            return True
        return False
    
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
        draw_y = y - 30 + math.sin(self.timer * 3.5) * 8
        
        # Draw as a triangle (upside-down pyramid shape)
        triangle_height = 20
        triangle_width = 16
        
        points = [
            (x, draw_y - triangle_height // 2),  # Top point
            (x - triangle_width // 2, draw_y + triangle_height // 2),  # Bottom left
            (x + triangle_width // 2, draw_y + triangle_height // 2)   # Bottom right
        ]
        
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, (255, 255, 255), points, 2)  # White outline
        
        # Draw pulsing effect if not ready to collect
        if self.collect_delay > 0:
            pulse_alpha = int(128 + 127 * math.sin(self.timer * 10))
            pulse_surface = pygame.Surface((triangle_width + 10, triangle_height + 10), pygame.SRCALPHA)
            pygame.draw.polygon(pulse_surface, (*color[:3], pulse_alpha), [
                (triangle_width // 2 + 5, triangle_height // 2 + 5),
                (5, triangle_height + 5),
                (triangle_width + 5, triangle_height + 5)
            ])
            screen.blit(pulse_surface, (x - triangle_width // 2 - 5, draw_y - triangle_height // 2 - 5))

        # Item name (only show when close to being collectable)
        if self.collect_delay < 0.2:
            font = pygame.font.Font(None, 18)
            text = font.render(self.item.name, True, (255, 255, 255))
            screen.blit(
                text,
                (x - text.get_width() // 2, draw_y - triangle_height - 20)
            )